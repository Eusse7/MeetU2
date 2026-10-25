"""
Composition Root del contexto Social.

Unico punto de configuracion donde se inyectan los adaptadores concretos a los
servicios del modulo.
"""
from apps.shared.infrastructure.unit_of_work import DjangoUnitOfWork
from apps.social.application.services import (
    CrearResenaService,
    ListarResenasExperienciaService,
    ListarResenasOrganizadorService,
    ListarResenasRecientesService,
    ListarResenasUsuarioService,
    ObtenerMetricasExperienciaService,
    ObtenerMetricasOrganizadorService,
    ObtenerResenaDeReservaService,
    ObtenerResenaService,
)
from apps.social.infrastructure.adapters import (
    IdentidadOrganizadorCalificacionAdapter,
    ReservaAsistenciaAdapter,
)
from apps.social.infrastructure.repositories import DjangoResenaRepository


def crear_resena() -> CrearResenaService:
    return CrearResenaService(
        resenas=DjangoResenaRepository(),
        asistencia=ReservaAsistenciaAdapter(),
        calificaciones_organizador=IdentidadOrganizadorCalificacionAdapter(),
        uow=DjangoUnitOfWork(),
    )


def obtener_resena() -> ObtenerResenaService:
    return ObtenerResenaService(resenas=DjangoResenaRepository())


def obtener_resena_de_reserva() -> ObtenerResenaDeReservaService:
    return ObtenerResenaDeReservaService(resenas=DjangoResenaRepository())


def listar_resenas_experiencia() -> ListarResenasExperienciaService:
    return ListarResenasExperienciaService(resenas=DjangoResenaRepository())


def listar_resenas_organizador() -> ListarResenasOrganizadorService:
    return ListarResenasOrganizadorService(resenas=DjangoResenaRepository())


def listar_resenas_usuario() -> ListarResenasUsuarioService:
    return ListarResenasUsuarioService(resenas=DjangoResenaRepository())


def listar_resenas_recientes() -> ListarResenasRecientesService:
    return ListarResenasRecientesService(resenas=DjangoResenaRepository())


def obtener_metricas_organizador() -> ObtenerMetricasOrganizadorService:
    return ObtenerMetricasOrganizadorService(resenas=DjangoResenaRepository())


def obtener_metricas_experiencia() -> ObtenerMetricasExperienciaService:
    return ObtenerMetricasExperienciaService(resenas=DjangoResenaRepository())
