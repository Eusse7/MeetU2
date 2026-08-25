"""Errores del contexto Reservas."""
from apps.shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


class ReservaNoEncontrada(NotFoundError):
    codigo = "reserva_no_encontrada"


class DatosReservaInvalidos(ValidationError):
    codigo = "datos_reserva_invalidos"


class TransicionReservaInvalida(ConflictError):
    codigo = "transicion_reserva_invalida"


class ReservaExpirada(ConflictError):
    codigo = "reserva_expirada"


class ReservaDuplicada(ConflictError):
    codigo = "reserva_duplicada"


class CheckInFueraDeVentana(ConflictError):
    codigo = "check_in_fuera_de_ventana"


class UsuarioNoAutorizado(ConflictError):
    codigo = "usuario_no_autorizado"


class CodigoTicketInvalido(NotFoundError):
    codigo = "codigo_ticket_invalido"
