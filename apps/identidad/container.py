"""
Composition Root del contexto Identidad.

Es el unico lugar donde se decide *que* implementacion concreta recibe cada
servicio. Las vistas piden un caso de uso ya armado y no conocen ni un
repositorio; los tests construyen los mismos servicios con dobles de prueba.
"""
from apps.identidad.application.services import (
    BuscarUsuarioPorCorreoService,
    ConvertirEnOrganizadorService,
    DesvincularInteresService,
    ListarInteresesService,
    ObtenerOrganizadorDeUsuarioService,
    ObtenerOrganizadorService,
    ObtenerUsuarioService,
    RegistrarUsuarioService,
    VerificarOrganizadorService,
    VincularInteresService,
)
from apps.identidad.infrastructure.adapters import CatalogoCategoriasAdapter
from apps.identidad.infrastructure.repositories import (
    DjangoInteresRepository,
    DjangoOrganizadorRepository,
    DjangoUsuarioRepository,
)
from apps.shared.infrastructure.unit_of_work import DjangoUnitOfWork


def registrar_usuario() -> RegistrarUsuarioService:
    return RegistrarUsuarioService(usuarios=DjangoUsuarioRepository())


def obtener_usuario() -> ObtenerUsuarioService:
    return ObtenerUsuarioService(usuarios=DjangoUsuarioRepository())


def buscar_usuario_por_correo() -> BuscarUsuarioPorCorreoService:
    return BuscarUsuarioPorCorreoService(usuarios=DjangoUsuarioRepository())


def convertir_en_organizador() -> ConvertirEnOrganizadorService:
    return ConvertirEnOrganizadorService(
        usuarios=DjangoUsuarioRepository(),
        organizadores=DjangoOrganizadorRepository(),
        uow=DjangoUnitOfWork(),
    )


def verificar_organizador() -> VerificarOrganizadorService:
    return VerificarOrganizadorService(organizadores=DjangoOrganizadorRepository())


def obtener_organizador() -> ObtenerOrganizadorService:
    return ObtenerOrganizadorService(organizadores=DjangoOrganizadorRepository())


def obtener_organizador_de_usuario() -> ObtenerOrganizadorDeUsuarioService:
    return ObtenerOrganizadorDeUsuarioService(
        organizadores=DjangoOrganizadorRepository()
    )


def vincular_interes() -> VincularInteresService:
    return VincularInteresService(
        usuarios=DjangoUsuarioRepository(),
        intereses=DjangoInteresRepository(),
        categorias=CatalogoCategoriasAdapter(),
    )


def listar_intereses() -> ListarInteresesService:
    return ListarInteresesService(intereses=DjangoInteresRepository())


def desvincular_interes() -> DesvincularInteresService:
    return DesvincularInteresService(intereses=DjangoInteresRepository())
