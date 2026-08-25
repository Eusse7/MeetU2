"""Composition Root del contexto Catalogo."""
from apps.catalogo.application.services import (
    BuscarExperienciasService,
    CancelarExperienciaService,
    CrearCategoriaService,
    CrearUbicacionService,
    GestionCupoService,
    ListarCategoriasService,
    ListarExperienciasOrganizadorService,
    ListarUbicacionesService,
    ObtenerExperienciaService,
    PublicarExperienciaService,
    RecomendarExperienciasService,
)
from apps.catalogo.infrastructure.adapters import (
    IdentidadInteresesAdapter,
    IdentidadOrganizadorAdapter,
)
from apps.shared.infrastructure.unit_of_work import DjangoUnitOfWork
from apps.catalogo.infrastructure.repositories import (
    DjangoCategoriaRepository,
    DjangoExperienciaRepository,
    DjangoUbicacionRepository,
)


def crear_ubicacion() -> CrearUbicacionService:
    return CrearUbicacionService(ubicaciones=DjangoUbicacionRepository())


def listar_ubicaciones() -> ListarUbicacionesService:
    return ListarUbicacionesService(ubicaciones=DjangoUbicacionRepository())


def crear_categoria() -> CrearCategoriaService:
    return CrearCategoriaService(categorias=DjangoCategoriaRepository())


def listar_categorias() -> ListarCategoriasService:
    return ListarCategoriasService(categorias=DjangoCategoriaRepository())


def publicar_experiencia() -> PublicarExperienciaService:
    return PublicarExperienciaService(
        experiencias=DjangoExperienciaRepository(),
        ubicaciones=DjangoUbicacionRepository(),
        categorias=DjangoCategoriaRepository(),
        organizadores=IdentidadOrganizadorAdapter(),
        uow=DjangoUnitOfWork(),
    )


def buscar_experiencias() -> BuscarExperienciasService:
    return BuscarExperienciasService(experiencias=DjangoExperienciaRepository())


def obtener_experiencia() -> ObtenerExperienciaService:
    return ObtenerExperienciaService(experiencias=DjangoExperienciaRepository())


def listar_experiencias_organizador() -> ListarExperienciasOrganizadorService:
    return ListarExperienciasOrganizadorService(
        experiencias=DjangoExperienciaRepository()
    )


def recomendar_experiencias() -> RecomendarExperienciasService:
    return RecomendarExperienciasService(
        experiencias=DjangoExperienciaRepository(),
        intereses=IdentidadInteresesAdapter(),
    )


def cancelar_experiencia() -> CancelarExperienciaService:
    return CancelarExperienciaService(
        experiencias=DjangoExperienciaRepository(),
        organizadores=IdentidadOrganizadorAdapter(),
    )


def gestion_cupo() -> GestionCupoService:
    """Lo consume el contexto Reservas a traves de su propio adaptador."""
    return GestionCupoService(experiencias=DjangoExperienciaRepository())
