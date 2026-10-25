"""Errores del contexto Social. El handler de DRF los traduce a HTTP."""
from apps.shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


class ResenaNoEncontrada(NotFoundError):
    codigo = "resena_no_encontrada"


class ReservaNoEncontrada(NotFoundError):
    codigo = "reserva_no_encontrada"


class ReservaSinCheckIn(ConflictError):
    codigo = "reserva_sin_check_in"


class ResenaDuplicada(ConflictError):
    codigo = "resena_duplicada"


class ReservaNoPerteneceAUsuario(ConflictError):
    codigo = "reserva_no_pertenece_a_usuario"


class CalificacionInvalida(ValidationError):
    codigo = "calificacion_invalida"
