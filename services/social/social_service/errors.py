"""Errores de dominio del microservicio Social."""


class ErrorDominioSocial(Exception):
    """Clase base de errores de dominio del contexto Social."""


class ResenaYaExisteError(ErrorDominioSocial):
    def __init__(self, reserva_id: str):
        super().__init__(f"Ya existe una reseña para la reserva {reserva_id}")
        self.reserva_id = reserva_id


class CalificacionInvalidaError(ErrorDominioSocial):
    def __init__(self, calificacion: int):
        super().__init__(f"Calificacion invalida: {calificacion}. Debe estar entre 1 y 5.")
        self.calificacion = calificacion


class ReservaNoAptaError(ErrorDominioSocial):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)


class ResenaNoEncontradaError(ErrorDominioSocial):
    def __init__(self, resena_id: str):
        super().__init__(f"No se encontro la reseña {resena_id}")
        self.resena_id = resena_id
