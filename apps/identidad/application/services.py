from uuid import UUID

from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
)
from apps.identidad.application.ports import (
    OrganizadorRepositoryPort,
    UsuarioRepositoryPort,
)
from apps.identidad.domain.exceptions import (
    CorreoYaRegistrado,
    OrganizadorNoEncontrado,
    UsuarioNoEncontrado,
    YaEsOrganizador,
)
from apps.identidad.domain.models import Organizador, Usuario
from apps.shared.application.unit_of_work import unit_of_work
from apps.shared.domain.enums import EstadoValidacion, TipoPerfil


class RegistrarUsuarioService:
    """Alta de un usuario asistente."""

    def __init__(self, usuarios: UsuarioRepositoryPort):
        self._usuarios = usuarios

    def ejecutar(self, dto: RegistrarUsuarioDTO) -> Usuario:
        correo = dto.correo.strip().lower()
        if self._usuarios.existe_correo(correo):
            raise CorreoYaRegistrado(f"El correo {correo} ya está registrado")

        usuario = Usuario(
            nombre=dto.nombre.strip(),
            correo=correo,
            tipo_perfil=TipoPerfil.ASISTENTE,
        )
        return self._usuarios.guardar(usuario)


class ConvertirEnOrganizadorService:
    """Crea el perfil de organizador para un usuario existente."""

    def __init__(
        self,
        usuarios: UsuarioRepositoryPort,
        organizadores: OrganizadorRepositoryPort,
    ):
        self._usuarios = usuarios
        self._organizadores = organizadores

    def ejecutar(self, dto: ConvertirEnOrganizadorDTO) -> Organizador:
        id_usuario = UUID(dto.id_usuario)
        usuario = self._usuarios.obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe el usuario {id_usuario}")

        if self._organizadores.obtener_por_usuario(id_usuario) is not None:
            raise YaEsOrganizador("El usuario ya tiene un perfil de organizador")

        with unit_of_work():
            organizador = Organizador(
                usuario=usuario,
                nombre_comercial=dto.nombre_comercial.strip(),
                cuenta_bancaria=dto.cuenta_bancaria,
                estado_verificacion=EstadoValidacion.PENDIENTE,
            )
            organizador = self._organizadores.guardar(organizador)

            usuario.tipo_perfil = TipoPerfil.ORGANIZADOR
            self._usuarios.guardar(usuario)

        return organizador


class VerificarOrganizadorService:
    """Aprueba o rechaza la verificación de un organizador."""

    def __init__(self, organizadores: OrganizadorRepositoryPort):
        self._organizadores = organizadores

    def ejecutar(self, id_organizador: UUID, aprobado: bool) -> Organizador:
        organizador = self._organizadores.obtener_por_id(id_organizador)
        if organizador is None:
            raise OrganizadorNoEncontrado(f"No existe el organizador {id_organizador}")

        organizador.estado_verificacion = (
            EstadoValidacion.VERIFICADO if aprobado else EstadoValidacion.RECHAZADO
        )
        return self._organizadores.guardar(organizador)