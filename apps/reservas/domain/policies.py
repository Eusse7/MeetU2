"""
Reglas de negocio puras del contexto Reservas.

Aqui vive el conocimiento que define el producto: cuanto se cobra, cuanto se
devuelve, cuando caduca una reserva y que transiciones son legales. Todo son
funciones sin estado sobre tipos primitivos, asi que se prueban sin Django,
sin base de datos y sin HTTP.
"""
import secrets
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from apps.reservas.domain.enums import EstadoReserva
from apps.reservas.domain.exceptions import (
    CheckInFueraDeVentana,
    DatosReservaInvalidos,
    TransicionReservaInvalida,
)

CENTAVOS = Decimal("0.01")
ALFABETO_TICKET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin caracteres ambiguos
LONGITUD_TICKET = 8


class CalculadoraMontos:
    """Aritmetica del cobro: total, comision de plataforma y neto del host."""

    @staticmethod
    def calcular_total(precio_unitario: Decimal, cantidad: int) -> Decimal:
        if cantidad <= 0:
            raise DatosReservaInvalidos("La cantidad de cupos debe ser positiva")
        if precio_unitario < 0:
            raise DatosReservaInvalidos("El precio unitario no puede ser negativo")
        return (Decimal(precio_unitario) * cantidad).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calcular_comision(monto_total: Decimal, porcentaje: Decimal) -> Decimal:
        if not Decimal("0") <= porcentaje <= Decimal("1"):
            raise DatosReservaInvalidos(
                "La comision de plataforma debe expresarse entre 0 y 1"
            )
        return (Decimal(monto_total) * porcentaje).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calcular_neto_organizador(
        monto_total: Decimal, comision: Decimal
    ) -> Decimal:
        return (Decimal(monto_total) - Decimal(comision)).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP
        )


class PoliticaCupos:
    """Cuantos cupos puede tomar una sola persona."""

    @staticmethod
    def validar_cantidad(cantidad: int, maximo_por_reserva: int) -> int:
        if cantidad <= 0:
            raise DatosReservaInvalidos("Debe reservar al menos un cupo")
        if cantidad > maximo_por_reserva:
            raise DatosReservaInvalidos(
                f"No se pueden reservar mas de {maximo_por_reserva} cupos "
                f"en una sola solicitud"
            )
        return cantidad


class PoliticaExpiracion:
    """Una reserva sin pagar retiene cupo solo por una ventana limitada."""

    @staticmethod
    def calcular_vencimiento(creada_en: datetime, minutos: int) -> datetime:
        return creada_en + timedelta(minutes=minutos)

    @staticmethod
    def esta_vencida(vence_en: datetime | None, ahora: datetime) -> bool:
        return vence_en is not None and ahora > vence_en


class PoliticaCancelacion:
    """
    Escala de reembolso segun la antelacion con que se cancela.

    Es la regla que hace sostenible el marketplace: cuanto mas cerca del evento
    se cancela, mas dano hace al organizador y menos se devuelve.
    """

    ESCALA: tuple[tuple[int, Decimal], ...] = (
        (48, Decimal("1.00")),   # 48 h o mas de antelacion -> 100 %
        (24, Decimal("0.50")),   # entre 24 y 48 h          ->  50 %
        (0, Decimal("0.00")),    # menos de 24 h            ->   0 %
    )

    @classmethod
    def porcentaje_reembolso(
        cls, fecha_experiencia: datetime, momento_cancelacion: datetime
    ) -> Decimal:
        horas = (fecha_experiencia - momento_cancelacion).total_seconds() / 3600
        for umbral, porcentaje in cls.ESCALA:
            if horas >= umbral:
                return porcentaje
        return Decimal("0.00")

    @classmethod
    def calcular_reembolso(
        cls,
        monto_pagado: Decimal,
        fecha_experiencia: datetime,
        momento_cancelacion: datetime,
    ) -> Decimal:
        porcentaje = cls.porcentaje_reembolso(fecha_experiencia, momento_cancelacion)
        return (Decimal(monto_pagado) * porcentaje).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def reembolso_total_por_cancelacion_del_organizador(
        monto_pagado: Decimal,
    ) -> Decimal:
        """Si cancela el host, el asistente nunca pierde dinero."""
        return Decimal(monto_pagado).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


class MaquinaEstadosReserva:
    """Transiciones legales de una reserva. Fuera de aqui, ninguna es valida."""

    TRANSICIONES: dict[str, set[str]] = {
        EstadoReserva.PENDIENTE_PAGO: {
            EstadoReserva.CONFIRMADA,
            EstadoReserva.CANCELADA,
            EstadoReserva.EXPIRADA,
        },
        EstadoReserva.CONFIRMADA: {
            EstadoReserva.CHECK_IN,
            EstadoReserva.CANCELADA,
            EstadoReserva.NO_ASISTIO,
        },
        EstadoReserva.CHECK_IN: set(),
        EstadoReserva.CANCELADA: set(),
        EstadoReserva.EXPIRADA: set(),
        EstadoReserva.NO_ASISTIO: set(),
    }

    #: Estados que mantienen un cupo retenido en la experiencia.
    ESTADOS_QUE_RETIENEN_CUPO = frozenset(
        {
            EstadoReserva.PENDIENTE_PAGO,
            EstadoReserva.CONFIRMADA,
            EstadoReserva.CHECK_IN,
            EstadoReserva.NO_ASISTIO,
        }
    )

    @classmethod
    def validar_transicion(cls, actual: str, nuevo: str) -> None:
        if nuevo not in cls.TRANSICIONES.get(actual, set()):
            raise TransicionReservaInvalida(
                f"Una reserva en estado {actual} no puede pasar a {nuevo}"
            )

    @classmethod
    def retiene_cupo(cls, estado: str) -> bool:
        return estado in cls.ESTADOS_QUE_RETIENEN_CUPO

    @staticmethod
    def es_cancelable(estado: str) -> bool:
        return estado in {EstadoReserva.PENDIENTE_PAGO, EstadoReserva.CONFIRMADA}


class PoliticaCheckIn:
    """
    Ventana de asistencia: solo se valida la presencia alrededor del evento.

    Sin esta regla cualquiera podria marcar asistencia semanas antes y dejar
    una resena sin haber ido (integridad de la reputacion).
    """

    @staticmethod
    def validar_ventana(
        fecha_experiencia: datetime, ahora: datetime, horas_ventana: int
    ) -> None:
        margen = timedelta(hours=horas_ventana)
        if ahora < fecha_experiencia - margen:
            raise CheckInFueraDeVentana(
                f"El check-in se habilita {horas_ventana} horas antes del evento"
            )
        if ahora > fecha_experiencia + margen:
            raise CheckInFueraDeVentana(
                "La ventana de check-in de esta experiencia ya se cerro"
            )


class GeneradorTicket:
    """Codigo corto e irrepetible que el asistente presenta en la puerta."""

    @staticmethod
    def generar() -> str:
        return "".join(
            secrets.choice(ALFABETO_TICKET) for _ in range(LONGITUD_TICKET)
        )
