"""Errores del contexto Identidad. El handler de DRF los traduce a HTTP."""
from apps.shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


class UsuarioNoEncontrado(NotFoundError):
    codigo = "usuario_no_encontrado"


class OrganizadorNoEncontrado(NotFoundError):
    codigo = "organizador_no_encontrado"


class CorreoYaRegistrado(ConflictError):
    codigo = "correo_ya_registrado"


class YaEsOrganizador(ConflictError):
    codigo = "ya_es_organizador"


class OrganizadorNoVerificado(ConflictError):
    codigo = "organizador_no_verificado"


class UsuarioInactivo(ConflictError):
    codigo = "usuario_inactivo"


class DatosPerfilInvalidos(ValidationError):
    codigo = "datos_perfil_invalidos"
