"""
Capa de aplicacion del contexto Identidad: un caso de uso por servicio (SRP).
"""
from uuid import UUID

from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
    VincularInteresDTO,
)
from apps.identidad.application.ports import (
    CatalogoCategoriasPort,
    InteresRepositoryPort,
    OrganizadorRepositoryPort,
    UsuarioRepositoryPort,
)
from apps.identidad.domain.exceptions import (
    CorreoYaRegistrado,
    DatosPerfilInvalidos,
    OrganizadorNoEncontrado,
    UsuarioNoEncontrado,
    YaEsOrganizador,
)
from apps.identidad.domain.models import InteresUsuario, Organizador, Usuario
from apps.identidad.domain.policies import (
    PoliticaIntereses,
    PoliticaRegistro,
    PoliticaVerificacion,
)
from apps.shared.application.unit_of_work import SinTransaccion, UnitOfWorkPort
from apps.shared.domain.enums import EstadoValidacion, TipoPerfil


class RegistrarUsuarioService:
    """Alta de un usuario asistente."""

    def __init__(self, usuarios: UsuarioRepositoryPort):
        self._usuarios = usuarios

    def ejecutar(self, dto: RegistrarUsuarioDTO) -> Usuario:
        correo = PoliticaRegistro.normalizar_correo(dto.correo)
        nombre = PoliticaRegistro.normalizar_nombre(dto.nombre)

        if self._usuarios.existe_correo(correo):
            raise CorreoYaRegistrado(f"El correo {correo} ya esta registrado")

        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            tipo_perfil=TipoPerfil.ASISTENTE,
        )
        return self._usuarios.guardar(usuario)


class ObtenerUsuarioService:
    def __init__(self, usuarios: UsuarioRepositoryPort):
        self._usuarios = usuarios

    def ejecutar(self, id_usuario: UUID) -> Usuario:
        usuario = self._usuarios.obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe el usuario {id_usuario}")
        return usuario


class BuscarUsuarioPorCorreoService:
    """Sustituye a un login real mientras no hay autenticacion (Entrega 2)."""

    def __init__(self, usuarios: UsuarioRepositoryPort):
        self._usuarios = usuarios

    def ejecutar(self, correo: str) -> Usuario:
        normalizado = PoliticaRegistro.normalizar_correo(correo)
        usuario = self._usuarios.obtener_por_correo(normalizado)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe un usuario con correo {normalizado}")
        return usuario


class ConvertirEnOrganizadorService:
    """Crea el perfil de organizador para un usuario existente."""

    def __init__(
        self,
        usuarios: UsuarioRepositoryPort,
        organizadores: OrganizadorRepositoryPort,
        uow: UnitOfWorkPort | None = None,
    ):
        self._usuarios = usuarios
        self._organizadores = organizadores
        self._uow = uow or SinTransaccion()

    def ejecutar(self, dto: ConvertirEnOrganizadorDTO) -> Organizador:
        usuario = self._usuarios.obtener_por_id(dto.id_usuario)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe el usuario {dto.id_usuario}")

        if self._organizadores.obtener_por_usuario(dto.id_usuario) is not None:
            raise YaEsOrganizador("El usuario ya tiene un perfil de organizador")

        nombre_comercial = (dto.nombre_comercial or "").strip()
        if len(nombre_comercial) < 3:
            raise DatosPerfilInvalidos(
                "El nombre comercial debe tener al menos 3 caracteres"
            )

        with self._uow:
            organizador = self._organizadores.guardar(
                Organizador(
                    usuario=usuario,
                    nombre_comercial=nombre_comercial,
                    cuenta_bancaria=dto.cuenta_bancaria.strip(),
                    estado_verificacion=EstadoValidacion.PENDIENTE,
                )
            )
            usuario.tipo_perfil = TipoPerfil.ORGANIZADOR
            self._usuarios.guardar(usuario)

        return organizador


class VerificarOrganizadorService:
    """Aprueba o rechaza la verificacion de un organizador (backoffice)."""

    def __init__(self, organizadores: OrganizadorRepositoryPort):
        self._organizadores = organizadores

    def ejecutar(self, id_organizador: UUID, aprobado: bool) -> Organizador:
        organizador = self._organizadores.obtener_por_id(id_organizador)
        if organizador is None:
            raise OrganizadorNoEncontrado(f"No existe el organizador {id_organizador}")

        organizador.estado_verificacion = PoliticaVerificacion.resolver_estado(aprobado)
        return self._organizadores.guardar(organizador)


class ObtenerOrganizadorService:
    def __init__(self, organizadores: OrganizadorRepositoryPort):
        self._organizadores = organizadores

    def ejecutar(self, id_organizador: UUID) -> Organizador:
        organizador = self._organizadores.obtener_por_id(id_organizador)
        if organizador is None:
            raise OrganizadorNoEncontrado(f"No existe el organizador {id_organizador}")
        return organizador


class ObtenerOrganizadorDeUsuarioService:
    """Devuelve el perfil de organizador de un usuario, o None si no lo tiene."""

    def __init__(self, organizadores: OrganizadorRepositoryPort):
        self._organizadores = organizadores

    def ejecutar(self, id_usuario: UUID) -> Organizador | None:
        return self._organizadores.obtener_por_usuario(id_usuario)


class VincularInteresService:
    """
    Caso de uso `vincularInteres` del modelo de dominio: el usuario declara que
    tan afin le resulta una categoria. Alimenta la recomendacion del catalogo.
    """

    def __init__(
        self,
        usuarios: UsuarioRepositoryPort,
        intereses: InteresRepositoryPort,
        categorias: CatalogoCategoriasPort,
    ):
        self._usuarios = usuarios
        self._intereses = intereses
        self._categorias = categorias

    def ejecutar(self, dto: VincularInteresDTO) -> InteresUsuario:
        if self._usuarios.obtener_por_id(dto.id_usuario) is None:
            raise UsuarioNoEncontrado(f"No existe el usuario {dto.id_usuario}")
        if not self._categorias.existe_categoria(dto.id_categoria):
            raise DatosPerfilInvalidos(
                f"No existe la categoria de interes {dto.id_categoria}"
            )

        nivel = PoliticaIntereses.validar_nivel(dto.nivel_afinidad)

        # Vincular dos veces la misma categoria actualiza el nivel (idempotente).
        interes = self._intereses.obtener(dto.id_usuario, dto.id_categoria)
        if interes is None:
            interes = InteresUsuario(
                usuario_id=dto.id_usuario,
                categoria_id=dto.id_categoria,
                nivel_afinidad=nivel,
            )
        else:
            interes.nivel_afinidad = nivel

        return self._intereses.guardar(interes)


class ListarInteresesService:
    def __init__(self, intereses: InteresRepositoryPort):
        self._intereses = intereses

    def ejecutar(self, id_usuario: UUID) -> list[InteresUsuario]:
        return self._intereses.listar_por_usuario(id_usuario)


class DesvincularInteresService:
    def __init__(self, intereses: InteresRepositoryPort):
        self._intereses = intereses

    def ejecutar(self, id_usuario: UUID, id_categoria: UUID) -> None:
        if not self._intereses.eliminar(id_usuario, id_categoria):
            raise UsuarioNoEncontrado(
                "El usuario no tiene vinculada esa categoria de interes"
            )
