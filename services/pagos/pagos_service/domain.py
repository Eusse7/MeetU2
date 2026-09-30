"""
Dominio del contexto Pagos: entidad y reglas puras.

No depende de Flask ni de SQLAlchemy, igual que el `domain/` de cada modulo del
monolito. Todo es aritmetica y transiciones sobre tipos primitivos, por lo que
se prueba sin base de datos ni HTTP.
"""
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pagos_service.errors import ConflictoPago, DatosInvalidos

CENTAVOS = Decimal("0.01")
ALFABETO_REFERENCIA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class EstadoPago(StrEnum):
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    REEMBOLSADO = "REEMBOLSADO"
    REEMBOLSO_PARCIAL = "REEMBOLSO_PARCIAL"


class MedioPago(StrEnum):
    TARJETA = "TARJETA"
    PSE = "PSE"
    NEQUI = "NEQUI"


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def dinero(valor) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


@dataclass
class Pago:
    id_reserva: UUID
    id_usuario: UUID
    id_organizador: UUID
    monto: Decimal
    comision_plataforma: Decimal
    medio_pago: MedioPago
    pasarela: str
    estado: EstadoPago
    referencia: str
    referencia_pasarela: str = ""
    motivo_rechazo: str = ""
    monto_reembolsado: Decimal = Decimal("0.00")
    reserva_confirmada: bool = False
    moneda: str = "COP"
    id: UUID = field(default_factory=uuid4)
    creado_en: datetime = field(default_factory=ahora_utc)
    actualizado_en: datetime = field(default_factory=ahora_utc)

    @property
    def neto_organizador(self) -> Decimal:
        return CalculadoraLiquidacion.neto_organizador(
            self.monto, self.comision_plataforma, self.monto_reembolsado
        )

    def como_dict(self) -> dict:
        return {
            "id": str(self.id),
            "id_reserva": str(self.id_reserva),
            "id_usuario": str(self.id_usuario),
            "id_organizador": str(self.id_organizador),
            "referencia": self.referencia,
            "referencia_pasarela": self.referencia_pasarela,
            "pasarela": self.pasarela,
            "medio_pago": str(self.medio_pago),
            "moneda": self.moneda,
            "monto": str(self.monto),
            "comision_plataforma": str(self.comision_plataforma),
            "monto_reembolsado": str(self.monto_reembolsado),
            "neto_organizador": str(self.neto_organizador),
            "estado": str(self.estado),
            "motivo_rechazo": self.motivo_rechazo,
            "reserva_confirmada": self.reserva_confirmada,
            "creado_en": self.creado_en.isoformat(),
            "actualizado_en": self.actualizado_en.isoformat(),
        }


class CalculadoraLiquidacion:
    """Cuanto recibe el organizador de cada cobro."""

    @staticmethod
    def neto_organizador(
        monto: Decimal, comision: Decimal, reembolsado: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Neto = lo cobrado - comision - lo devuelto al asistente.

        La comision de plataforma no se devuelve en un reembolso parcial: la
        absorbe el organizador, que es quien retiene parte del dinero. Nunca
        puede ser negativo.
        """
        if monto <= 0 and reembolsado <= 0:
            return Decimal("0.00")
        if dinero(reembolsado) >= dinero(monto):
            return Decimal("0.00")
        neto = dinero(monto) - dinero(comision) - dinero(reembolsado)
        return max(neto, Decimal("0.00"))


class PoliticaPago:
    """Reglas que decide el microservicio antes de tocar la pasarela."""

    @staticmethod
    def validar_monto(monto: Decimal) -> Decimal:
        monto = dinero(monto)
        if monto <= 0:
            raise DatosInvalidos(
                "Una reserva gratuita no requiere pago", codigo="monto_invalido"
            )
        return monto

    @staticmethod
    def validar_medio(medio: str) -> MedioPago:
        try:
            return MedioPago((medio or "").strip().upper())
        except ValueError:
            validos = ", ".join(m.value for m in MedioPago)
            raise DatosInvalidos(
                f"Medio de pago no soportado. Usa uno de: {validos}",
                codigo="medio_pago_invalido",
            ) from None

    @staticmethod
    def validar_reembolso(pago: Pago, monto: Decimal) -> Decimal:
        monto = dinero(monto)
        if pago.estado not in {EstadoPago.APROBADO}:
            raise ConflictoPago(
                f"Un pago en estado {pago.estado} no admite reembolso",
                codigo="transicion_pago_invalida",
            )
        if monto <= 0:
            raise ConflictoPago(
                "La politica de cancelacion no otorga reembolso para esta reserva",
                codigo="sin_reembolso",
            )
        if monto > pago.monto:
            raise DatosInvalidos(
                "El reembolso no puede superar lo cobrado",
                codigo="reembolso_excedido",
            )
        return monto

    @staticmethod
    def estado_tras_reembolso(pago: Pago, monto: Decimal) -> EstadoPago:
        return (
            EstadoPago.REEMBOLSADO
            if dinero(monto) >= dinero(pago.monto)
            else EstadoPago.REEMBOLSO_PARCIAL
        )


class GeneradorReferencia:
    """Referencia legible y unica que viaja al monolito como comprobante."""

    @staticmethod
    def generar() -> str:
        sufijo = "".join(secrets.choice(ALFABETO_REFERENCIA) for _ in range(10))
        return f"PAG-{sufijo}"
