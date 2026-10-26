"""Errores de dominio del microservicio de Catalogo."""


class ErrorDominioCatalogo(Exception):
    """Clase base de errores de Catalogo."""


class CupoExcedeAforoError(ErrorDominioCatalogo):
    def __init__(self, cupo: int, aforo: int):
        super().__init__(f"El cupo solicitado ({cupo}) excede el aforo maximo de la ubicacion ({aforo})")


class ExperienciaNoEncontradaError(ErrorDominioCatalogo):
    def __init__(self, exp_id: str):
        super().__init__(f"No se encontro la experiencia {exp_id}")


class UbicacionNoEncontradaError(ErrorDominioCatalogo):
    def __init__(self, ubi_id: str):
        super().__init__(f"No se encontro la ubicacion {ubi_id}")
