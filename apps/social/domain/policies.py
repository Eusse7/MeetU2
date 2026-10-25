"""
Reglas de negocio puras del contexto Social.

Define las politicas de calificacion: quien puede calificar (solo quien
asistio con reserva en estado CHECK_IN y check_in_en registrado), rango de
estrellas (1 a 5) y el calculo del promedio ponderado/aritmetico del organizador.
"""
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from apps.social.domain.exceptions import (
    CalificacionInvalida,
    ReservaNoPerteneceAUsuario,
    ReservaSinCheckIn,
)

DECIMAL_DOS = Decimal("0.01")


class PoliticaResena:
    """Valida los prerrequisitos para calificar una experiencia."""

    @staticmethod
    def validar_asistencia(
        id_usuario: UUID,
        reserva_usuario_id: UUID,
        reserva_estado: str,
        tiene_check_in: bool,
    ) -> None:
        if id_usuario != reserva_usuario_id:
            raise ReservaNoPerteneceAUsuario(
                "La reserva indicada pertenece a otro usuario"
            )
        if reserva_estado != "CHECK_IN" or not tiene_check_in:
            raise ReservaSinCheckIn(
                "Solo puede calificar una experiencia quien haya completado el check-in"
            )

    @staticmethod
    def validar_calificacion(calificacion: int) -> None:
        if not isinstance(calificacion, int) or calificacion < 1 or calificacion > 5:
            raise CalificacionInvalida(
                "La calificacion debe ser un numero entero entre 1 y 5"
            )


class CalculadoraPromedio:
    """Calcula el promedio de calificaciones redondeado a 2 decimales."""

    @staticmethod
    def calcular(calificaciones: list[int | Decimal | float]) -> Decimal:
        if not calificaciones:
            return Decimal("0.00")
        promedio = Decimal(str(sum(calificaciones))) / Decimal(str(len(calificaciones)))
        return promedio.quantize(DECIMAL_DOS, rounding=ROUND_HALF_UP)
