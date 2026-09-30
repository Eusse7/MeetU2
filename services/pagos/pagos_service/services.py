"""
Casos de uso del microservicio de Pagos.

Misma disciplina que la capa `application/` del monolito: los servicios reciben
sus dependencias por constructor (repositorio, pasarela, cliente del monolito)
y no conocen Flask. Por eso las pruebas los ejercitan con dobles en memoria.
"""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from pagos_service.domain import (
    CalculadoraLiquidacion,
    EstadoPago,
    GeneradorReferencia,
    Pago,
    PoliticaPago,
    dinero,
)
from pagos_service.errors import (
    ConflictoPago,
    PagoDuplicado,
    PagoNoEncontrado,
    PagoRechazado,
    ReservaNoPagable,
    ServicioNoDisponible,
    SinReembolso,
    UsuarioNoAutorizado,
)
from pagos_service.gateways import PasarelaPort
from pagos_service.repository import PagoRepositoryPort
from pagos_service.reservas_client import ReservasPort

ESTADO_RESERVA_PAGABLE = "PENDIENTE_PAGO"
ESTADO_RESERVA_CANCELADA = "CANCELADA"


@dataclass(frozen=True)
class ProcesarPagoDTO:
    id_reserva: UUID
    id_usuario: UUID
    medio_pago: str
    token_pago: str = ""


class ProcesarPagoService:
    """
    Cobra una reserva y la confirma en el monolito.

    Pasos:
      1. Traer la reserva de Django (fuente de verdad de monto y estado).
      2. Validar titular, estado PENDIENTE_PAGO y que no exista otro cobro.
      3. Cobrar en la pasarela elegida por la Factory.
      4. Persistir el pago (aprobado o rechazado) ANTES de avisar a Django,
         para que el monolito pueda verificar la referencia.
      5. Confirmar la reserva en Django con la referencia del pago.
      6. Si Django rechaza la confirmacion (p. ej. la reserva expiro mientras
         se cobraba) se ejecuta la compensacion: reembolso total. Es el patron
         Saga en su forma mas simple, sin transaccion distribuida.
    """

    def __init__(self, pagos: PagoRepositoryPort, pasarela: PasarelaPort,
                 reservas: ReservasPort):
        self._pagos = pagos
        self._pasarela = pasarela
        self._reservas = reservas

    def ejecutar(self, dto: ProcesarPagoDTO) -> Pago:
        medio = PoliticaPago.validar_medio(dto.medio_pago)
        reserva = self._reservas.obtener(dto.id_reserva)

        if reserva.usuario_id != dto.id_usuario:
            raise UsuarioNoAutorizado("Solo el titular de la reserva puede pagarla")
        if self._pagos.aprobado_de_reserva(reserva.id):
            raise PagoDuplicado("Esta reserva ya tiene un pago registrado")
        if reserva.estado != ESTADO_RESERVA_PAGABLE:
            raise ReservaNoPagable(
                f"Una reserva en estado {reserva.estado} no se puede pagar"
            )
        monto = PoliticaPago.validar_monto(reserva.monto_total)

        referencia = GeneradorReferencia.generar()
        resultado = self._pasarela.cobrar(referencia, monto, medio, dto.token_pago)

        pago = Pago(
            id_reserva=reserva.id,
            id_usuario=reserva.usuario_id,
            id_organizador=reserva.organizador_id,
            monto=monto,
            comision_plataforma=dinero(reserva.comision_plataforma),
            medio_pago=medio,
            pasarela=self._pasarela.nombre,
            estado=EstadoPago.APROBADO if resultado.aprobado else EstadoPago.RECHAZADO,
            referencia=referencia,
            referencia_pasarela=resultado.referencia_pasarela,
            motivo_rechazo=resultado.motivo,
        )
        self._pagos.guardar(pago)

        if not resultado.aprobado:
            raise PagoRechazado(
                resultado.motivo or "La pasarela rechazo el pago",
                detalle={"id_pago": str(pago.id), "referencia": pago.referencia},
            )

        try:
            self._reservas.confirmar(reserva.id, pago.referencia)
        except ConflictoPago as exc:
            self._compensar(pago, f"Compensacion: {exc.mensaje}")
            raise
        except ServicioNoDisponible:
            # No sabemos si Django alcanzo a confirmar: el pago queda APROBADO
            # con reserva_confirmada=False para conciliarlo despues.
            raise

        pago.reserva_confirmada = True
        return self._pagos.guardar(pago)

    def _compensar(self, pago: Pago, motivo: str) -> None:
        self._pasarela.reembolsar(pago.referencia_pasarela, pago.monto)
        pago.monto_reembolsado = pago.monto
        pago.estado = EstadoPago.REEMBOLSADO
        pago.motivo_rechazo = motivo
        self._pagos.guardar(pago)


class ReembolsarPagoService:
    """
    Devuelve al asistente lo que la politica de cancelacion del monolito
    decidio. El microservicio no recalcula el porcentaje: esa regla sigue
    siendo de Reservas; Pagos solo mueve el dinero.
    """

    def __init__(self, pagos: PagoRepositoryPort, pasarela: PasarelaPort,
                 reservas: ReservasPort):
        self._pagos = pagos
        self._pasarela = pasarela
        self._reservas = reservas

    def ejecutar(self, id_reserva: UUID) -> Pago:
        pago = self._pagos.aprobado_de_reserva(id_reserva)
        if pago is None:
            raise PagoNoEncontrado(f"La reserva {id_reserva} no tiene un pago aprobado")

        reserva = self._reservas.obtener(id_reserva)
        if reserva.estado != ESTADO_RESERVA_CANCELADA:
            raise ConflictoPago(
                "Solo se reembolsan reservas canceladas",
                codigo="reserva_no_cancelada",
            )
        if reserva.monto_reembolsado <= 0:
            raise SinReembolso(
                "La politica de cancelacion no otorga reembolso para esta reserva"
            )

        monto = PoliticaPago.validar_reembolso(pago, reserva.monto_reembolsado)
        self._pasarela.reembolsar(pago.referencia_pasarela, monto)

        pago.monto_reembolsado = monto
        pago.estado = PoliticaPago.estado_tras_reembolso(pago, monto)
        return self._pagos.guardar(pago)


class ConsultarPagosService:
    def __init__(self, pagos: PagoRepositoryPort):
        self._pagos = pagos

    def por_id(self, id_pago: UUID) -> Pago:
        pago = self._pagos.obtener_por_id(id_pago)
        if pago is None:
            raise PagoNoEncontrado(f"No existe el pago {id_pago}")
        return pago

    def por_referencia(self, referencia: str) -> Pago:
        pago = self._pagos.obtener_por_referencia(referencia.strip().upper())
        if pago is None:
            raise PagoNoEncontrado(f"No existe un pago con referencia {referencia}")
        return pago

    def listar(self, **filtros) -> list[Pago]:
        return self._pagos.listar(**filtros)


class LiquidacionOrganizadorService:
    """Cuanto se le debe desembolsar a un organizador (comision descontada)."""

    def __init__(self, pagos: PagoRepositoryPort):
        self._pagos = pagos

    def ejecutar(self, id_organizador: UUID) -> dict:
        cobrados = [
            p for p in self._pagos.listar(id_organizador=id_organizador)
            if p.estado != EstadoPago.RECHAZADO
        ]
        bruto = sum((p.monto for p in cobrados), Decimal("0.00"))
        reembolsos = sum((p.monto_reembolsado for p in cobrados), Decimal("0.00"))
        comisiones = sum(
            (p.comision_plataforma for p in cobrados if p.estado != EstadoPago.REEMBOLSADO),
            Decimal("0.00"),
        )
        neto = sum(
            (
                CalculadoraLiquidacion.neto_organizador(
                    p.monto, p.comision_plataforma, p.monto_reembolsado
                )
                for p in cobrados
            ),
            Decimal("0.00"),
        )
        return {
            "id_organizador": str(id_organizador),
            "pagos_considerados": len(cobrados),
            "total_cobrado": str(dinero(bruto)),
            "total_reembolsado": str(dinero(reembolsos)),
            "comision_plataforma": str(dinero(comisiones)),
            "neto_a_desembolsar": str(dinero(neto)),
            "moneda": "COP",
        }
