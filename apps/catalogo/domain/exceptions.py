"""Errores del contexto Catalogo. El handler de DRF los traduce a HTTP."""
from apps.shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


class ExperienciaNoEncontrada(NotFoundError):
    codigo = "experiencia_no_encontrada"


class UbicacionNoEncontrada(NotFoundError):
    codigo = "ubicacion_no_encontrada"


class CategoriaNoEncontrada(NotFoundError):
    codigo = "categoria_no_encontrada"


class DatosExperienciaInvalidos(ValidationError):
    codigo = "datos_experiencia_invalidos"


class AforoExcedido(ValidationError):
    codigo = "aforo_excedido"


class OrganizadorNoAutorizado(ConflictError):
    codigo = "organizador_no_autorizado"


class ExperienciaNoDisponible(ConflictError):
    codigo = "experiencia_no_disponible"


class CupoInsuficiente(ConflictError):
    codigo = "cupo_insuficiente"


class TransicionExperienciaInvalida(ConflictError):
    codigo = "transicion_experiencia_invalida"
