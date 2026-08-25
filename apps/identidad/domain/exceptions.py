# apps/identidad/domain/exceptions.py
from apps.shared.domain.exceptions import ConflictError, NotFoundError


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