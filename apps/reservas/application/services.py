"""
Capa de aplicacion del contexto Reservas.

`SolicitarReservaService` es la funcionalidad mas compleja del sistema: cruza
tres contextos (Identidad, Catalogo, Notificaciones), mueve inventario y debe
ser atomica. Su diagrama de secuencia esta en la Wiki (docs/wiki).
"""
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.utils import timezone

from apps.reservas.application.dtos import (
    CancelarReservaDTO,
    CheckInDTO,
    ConfirmarReservaDTO,
    ReservaDetalladaDTO,
    ResultadoCancelacionDTO,
    SolicitarReservaDTO,
)
from apps.reservas.application.ports import (
    CatalogoPort,
    NotificadorPort,
    PerfilUsuarioPort,
    ReservaRepositoryPort,
)
from apps.reservas.domain.enums import EstadoReserva, OrigenCancelacion
from apps.reservas.domain.exceptions import (
    CodigoTicketInvalido,
    DatosReservaInvalidos,
    ReservaDuplicada,
    ReservaExpirada,
    ReservaNoEncontrada,
    UsuarioNoAutorizado,
)
from apps.reservas.domain.models import Reserva
from apps.reservas.domain.policies import (
    CalculadoraMontos,
    GeneradorTicket,
    MaquinaEstadosReserva,
    PoliticaCancelacion,
    PoliticaCheckIn,
    PoliticaCupos,
    PoliticaExpiracion,
)
from apps.shared.application.unit_of_work import SinTransaccion, UnitOfWorkPort


class SolicitarReservaService:
    """
    Caso de uso central: un usuario toma cupos de una experiencia.

    Pasos:
      1. Verificar que el usuario existe y esta activo.
      2. Traer la experiencia del Catalogo (proyeccion de solo lectura).
      3. Aplicar las politicas de cupos y de reserva duplicada.
      4. Bloquear el cupo en Catalogo -- unico efecto sobre otro contexto.
      5. Calcular montos y emitir el ticket.
      6. Persistir. Los pasos 4 y 6 comparten transaccion: si falla el guardado,
         el cupo se devuelve solo (rollback) y no queda inventario fantasma.
      7. Notificar *fuera* de la transaccion: un canal caido no debe revertir
         una reserva valida.
    """

    def __init__(
        self,
        reservas: ReservaRepositoryPort,
        catalogo: CatalogoPort,
        perfiles: PerfilUsuarioPort,
        notificador: NotificadorPort,
        uow: UnitOfWorkPort | None = None,
        comision: Decimal | None = None,
        minutos_expiracion: int | None = None,
        max_cupos_por_reserva: int | None = None,
        reloj=timezone.now,
    ):
        self._reservas = reservas
        self._catalogo = catalogo
        self._perfiles = perfiles
        self._notificador = notificador
        self._uow = uow or SinTransaccion()
        self._comision = (
            comision if comision is not None else settings.COMISION_PLATAFORMA
        )
        self._minutos_expiracion = (
            minutos_expiracion
            if minutos_expiracion is not None
            else settings.MINUTOS_EXPIRACION_RESERVA
        )
        self._max_cupos = (
            max_cupos_por_reserva
            if max_cupos_por_reserva is not None
            else settings.MAX_CUPOS_POR_RESERVA
        )
        self._reloj = reloj

    def ejecutar(self, dto: SolicitarReservaDTO) -> Reserva:
        usuario = self._perfiles.obtener(dto.id_usuario)
        if usuario is None:
            raise ReservaNoEncontrada(f"No existe el usuario {dto.id_usuario}")
        if not usuario.activo:
            raise UsuarioNoAutorizado("El usuario esta inactivo y no puede reservar")

        experiencia = self._catalogo.obtener_experiencia(dto.id_experiencia)
        if experiencia is None:
            raise ReservaNoEncontrada(
                f"No existe la experiencia {dto.id_experiencia}"
            )

        cantidad = PoliticaCupos.validar_cantidad(dto.cantidad_cupos, self._max_cupos)

        if self._reservas.existe_activa(dto.id_usuario, dto.id_experiencia):
            raise ReservaDuplicada(
                "Ya tienes una reserva activa para esta experiencia"
            )

        ahora = self._reloj()
        if experiencia.fecha_hora <= ahora:
            raise DatosReservaInvalidos(
                "No se puede reservar una experiencia que ya ocurrio"
            )

        monto_total = CalculadoraMontos.calcular_total(experiencia.precio, cantidad)
        comision = CalculadoraMontos.calcular_comision(monto_total, self._comision)

        with self._uow:
            # Catalogo es el dueno del inventario: valida estado y disponibilidad.
            self._catalogo.bloquear_cupo(dto.id_experiencia, cantidad)

            reserva = Reserva(
                usuario_id=dto.id_usuario,
                experiencia_id=experiencia.id,
                organizador_id=experiencia.organizador_id,
                codigo_ticket=self._emitir_ticket(),
                cantidad_cupos=cantidad,
                precio_unitario=experiencia.precio,
                monto_total=monto_total,
                comision_plataforma=comision,
                estado=EstadoReserva.PENDIENTE_PAGO,
                vence_en=PoliticaExpiracion.calcular_vencimiento(
                    ahora, self._minutos_expiracion
                ),
            )
            reserva = self._reservas.guardar(reserva)

        self._notificador.reserva_creada(reserva, usuario, experiencia)
        return reserva

    def _emitir_ticket(self) -> str:
        for _ in range(5):
            codigo = GeneradorTicket.generar()
            if not self._reservas.existe_ticket(codigo):
                return codigo
        raise DatosReservaInvalidos(
            "No fue posible generar un codigo de ticket unico, reintenta"
        )


class ConfirmarReservaService:
    """
    Confirma una reserva tras el pago.

    Mientras el contexto Pagos no exista (Entrega 2), recibe la referencia de
    pago como dato opaco. Cuando exista, se inyecta un `PagoPort` y el resto de
    este servicio no cambia.
    """

    def __init__(
        self,
        reservas: ReservaRepositoryPort,
        catalogo: CatalogoPort,
        perfiles: PerfilUsuarioPort,
        notificador: NotificadorPort,
        uow: UnitOfWorkPort | None = None,
        reloj=timezone.now,
    ):
        self._reservas = reservas
        self._catalogo = catalogo
        self._perfiles = perfiles
        self._notificador = notificador
        self._uow = uow or SinTransaccion()
        self._reloj = reloj

    def ejecutar(self, dto: ConfirmarReservaDTO) -> Reserva:
        reserva = self._reservas.obtener_por_id(dto.id_reserva)
        if reserva is None:
            raise ReservaNoEncontrada(f"No existe la reserva {dto.id_reserva}")

        ahora = self._reloj()
        if PoliticaExpiracion.esta_vencida(reserva.vence_en, ahora):
            raise ReservaExpirada(
                "La ventana de pago expiro; el cupo fue liberado. Reserva de nuevo."
            )

        MaquinaEstadosReserva.validar_transicion(
            reserva.estado, EstadoReserva.CONFIRMADA
        )

        reserva.estado = EstadoReserva.CONFIRMADA
        reserva.confirmada_en = ahora
        reserva.vence_en = None
        reserva = self._reservas.guardar(reserva)

        usuario = self._perfiles.obtener(reserva.usuario_id)
        experiencia = self._catalogo.obtener_experiencia(reserva.experiencia_id)
        if usuario and experiencia:
            self._notificador.reserva_confirmada(reserva, usuario, experiencia)
        return reserva


class CancelarReservaService:
    """
    Cancela una reserva, devuelve el cupo al catalogo y calcula el reembolso
    segun la antelacion (PoliticaCancelacion).
    """

    def __init__(
        self,
        reservas: ReservaRepositoryPort,
        catalogo: CatalogoPort,
        perfiles: PerfilUsuarioPort,
        notificador: NotificadorPort,
        uow: UnitOfWorkPort | None = None,
        reloj=timezone.now,
    ):
        self._reservas = reservas
        self._catalogo = catalogo
        self._perfiles = perfiles
        self._notificador = notificador
        self._uow = uow or SinTransaccion()
        self._reloj = reloj

    def ejecutar(self, dto: CancelarReservaDTO) -> ResultadoCancelacionDTO:
        reserva = self._reservas.obtener_por_id(dto.id_reserva)
        if reserva is None:
            raise ReservaNoEncontrada(f"No existe la reserva {dto.id_reserva}")
        if str(reserva.usuario_id) != str(dto.id_usuario):
            raise UsuarioNoAutorizado("Solo el titular puede cancelar la reserva")

        MaquinaEstadosReserva.validar_transicion(
            reserva.estado, EstadoReserva.CANCELADA
        )

        ahora = self._reloj()
        experiencia = self._catalogo.obtener_experiencia(reserva.experiencia_id)
        fecha_evento = experiencia.fecha_hora if experiencia else ahora

        # Solo se reembolsa lo que efectivamente se cobro.
        monto_pagado = (
            reserva.monto_total
            if reserva.estado == EstadoReserva.CONFIRMADA
            else Decimal("0")
        )
        porcentaje = PoliticaCancelacion.porcentaje_reembolso(fecha_evento, ahora)
        reembolso = PoliticaCancelacion.calcular_reembolso(
            monto_pagado, fecha_evento, ahora
        )

        with self._uow:
            if MaquinaEstadosReserva.retiene_cupo(reserva.estado):
                self._catalogo.liberar_cupo(
                    reserva.experiencia_id, reserva.cantidad_cupos
                )

            reserva.estado = EstadoReserva.CANCELADA
            reserva.cancelada_en = ahora
            reserva.origen_cancelacion = OrigenCancelacion.USUARIO
            reserva.motivo_cancelacion = (dto.motivo or "").strip()[:255]
            reserva.monto_reembolsado = reembolso
            reserva.vence_en = None
            reserva = self._reservas.guardar(reserva)

        usuario = self._perfiles.obtener(reserva.usuario_id)
        if usuario:
            self._notificador.reserva_cancelada(reserva, usuario, reembolso)

        return ResultadoCancelacionDTO(
            reserva=reserva,
            monto_reembolsado=reembolso,
            porcentaje_aplicado=porcentaje,
        )


class RegistrarCheckInService:
    """
    El organizador valida el ticket el dia del evento.

    Habilita la resena posterior: sin check-in no hay calificacion (regla que
    protege la reputacion del marketplace).
    """

    def __init__(
        self,
        reservas: ReservaRepositoryPort,
        catalogo: CatalogoPort,
        horas_ventana: int | None = None,
        reloj=timezone.now,
    ):
        self._reservas = reservas
        self._catalogo = catalogo
        self._horas_ventana = (
            horas_ventana
            if horas_ventana is not None
            else settings.HORAS_VENTANA_CHECKIN
        )
        self._reloj = reloj

    def ejecutar(self, dto: CheckInDTO) -> Reserva:
        codigo = (dto.codigo_ticket or "").strip().upper()
        reserva = self._reservas.obtener_por_ticket(codigo)
        if reserva is None:
            raise CodigoTicketInvalido(f"No existe una reserva con el ticket {codigo}")
        if str(reserva.organizador_id) != str(dto.id_organizador):
            raise UsuarioNoAutorizado(
                "Solo el organizador de la experiencia puede registrar el check-in"
            )

        MaquinaEstadosReserva.validar_transicion(reserva.estado, EstadoReserva.CHECK_IN)

        experiencia = self._catalogo.obtener_experiencia(reserva.experiencia_id)
        ahora = self._reloj()
        if experiencia is not None:
            PoliticaCheckIn.validar_ventana(
                experiencia.fecha_hora, ahora, self._horas_ventana
            )

        reserva.estado = EstadoReserva.CHECK_IN
        reserva.check_in_en = ahora
        return self._reservas.guardar(reserva)


class ExpirarReservasVencidasService:
    """
    Tarea de mantenimiento: libera el cupo de las reservas que nadie pago.

    Hoy se dispara desde un comando de gestion; en produccion seria un job
    periodico (Celery beat). La logica no cambia.
    """

    def __init__(
        self,
        reservas: ReservaRepositoryPort,
        catalogo: CatalogoPort,
        uow: UnitOfWorkPort | None = None,
        reloj=timezone.now,
    ):
        self._reservas = reservas
        self._catalogo = catalogo
        self._uow = uow or SinTransaccion()
        self._reloj = reloj

    def ejecutar(self, pendientes: list[Reserva]) -> int:
        ahora = self._reloj()
        expiradas = 0

        for reserva in pendientes:
            if not PoliticaExpiracion.esta_vencida(reserva.vence_en, ahora):
                continue

            MaquinaEstadosReserva.validar_transicion(
                reserva.estado, EstadoReserva.EXPIRADA
            )
            with self._uow:
                self._catalogo.liberar_cupo(
                    reserva.experiencia_id, reserva.cantidad_cupos
                )
                reserva.estado = EstadoReserva.EXPIRADA
                reserva.vence_en = None
                self._reservas.guardar(reserva)
            expiradas += 1

        return expiradas


class ListarReservasUsuarioService:
    """
    Compone la vista 'Mis reservas': datos propios de Reservas enriquecidos con
    el titulo y la fecha que viven en Catalogo.

    Es exactamente el trabajo de composicion que, en una arquitectura de
    microservicios, haria un Backend-for-Frontend detras del API Gateway.
    """

    def __init__(self, reservas: ReservaRepositoryPort, catalogo: CatalogoPort):
        self._reservas = reservas
        self._catalogo = catalogo

    def ejecutar(self, id_usuario: UUID) -> list[ReservaDetalladaDTO]:
        detalladas = []
        for reserva in self._reservas.listar_por_usuario(id_usuario):
            experiencia = self._catalogo.obtener_experiencia(reserva.experiencia_id)
            detalladas.append(
                ReservaDetalladaDTO(
                    reserva=reserva,
                    experiencia_titulo=experiencia.titulo if experiencia else "",
                    experiencia_fecha=experiencia.fecha_hora if experiencia else None,
                    experiencia_ciudad=experiencia.ciudad if experiencia else "",
                )
            )
        return detalladas


class ObtenerReservaService:
    def __init__(self, reservas: ReservaRepositoryPort):
        self._reservas = reservas

    def ejecutar(self, id_reserva: UUID) -> Reserva:
        reserva = self._reservas.obtener_por_id(id_reserva)
        if reserva is None:
            raise ReservaNoEncontrada(f"No existe la reserva {id_reserva}")
        return reserva


class ListarReservasExperienciaService:
    """Panel del organizador: quien viene a mi evento."""

    def __init__(self, reservas: ReservaRepositoryPort):
        self._reservas = reservas

    def ejecutar(self, id_experiencia: UUID) -> list[Reserva]:
        return self._reservas.listar_por_experiencia(id_experiencia)
