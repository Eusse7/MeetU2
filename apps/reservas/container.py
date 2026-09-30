"""Composition Root del contexto Reservas."""
from django.conf import settings

from apps.reservas.application.services import (
    CancelarReservaService,
    ConfirmarReservaService,
    ExpirarReservasVencidasService,
    ListarReservasExperienciaService,
    ListarReservasUsuarioService,
    ObtenerReservaService,
    RegistrarCheckInService,
    SolicitarReservaService,
)
from apps.reservas.infrastructure.adapters import (
    CatalogoServiceAdapter,
    HttpVerificadorPago,
    IdentidadPerfilAdapter,
    NotificacionesAdapter,
)
from apps.reservas.infrastructure.repositories import DjangoReservaRepository
from apps.shared.infrastructure.unit_of_work import DjangoUnitOfWork


def solicitar_reserva() -> SolicitarReservaService:
    return SolicitarReservaService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
        perfiles=IdentidadPerfilAdapter(),
        notificador=NotificacionesAdapter(),
        uow=DjangoUnitOfWork(),
    )


def verificador_pago() -> HttpVerificadorPago | None:
    """
    Feature toggle del Strangler: con PAGOS_SERVICE_URL definido, la
    confirmacion exige un pago real del microservicio; sin el, se mantiene el
    comportamiento legado de /api/v1.
    """
    if not settings.PAGOS_SERVICE_URL:
        return None
    return HttpVerificadorPago(settings.PAGOS_SERVICE_URL)


def confirmar_reserva() -> ConfirmarReservaService:
    return ConfirmarReservaService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
        perfiles=IdentidadPerfilAdapter(),
        notificador=NotificacionesAdapter(),
        uow=DjangoUnitOfWork(),
        verificador_pago=verificador_pago(),
    )


def cancelar_reserva() -> CancelarReservaService:
    return CancelarReservaService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
        perfiles=IdentidadPerfilAdapter(),
        notificador=NotificacionesAdapter(),
        uow=DjangoUnitOfWork(),
    )


def registrar_check_in() -> RegistrarCheckInService:
    return RegistrarCheckInService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
    )


def listar_reservas_usuario() -> ListarReservasUsuarioService:
    return ListarReservasUsuarioService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
    )


def listar_reservas_experiencia() -> ListarReservasExperienciaService:
    return ListarReservasExperienciaService(reservas=DjangoReservaRepository())


def obtener_reserva() -> ObtenerReservaService:
    return ObtenerReservaService(reservas=DjangoReservaRepository())


def expirar_reservas_vencidas() -> ExpirarReservasVencidasService:
    return ExpirarReservasVencidasService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
        uow=DjangoUnitOfWork(),
    )
