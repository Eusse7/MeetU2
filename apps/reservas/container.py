"""Composition Root del contexto Reservas."""
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


def confirmar_reserva() -> ConfirmarReservaService:
    return ConfirmarReservaService(
        reservas=DjangoReservaRepository(),
        catalogo=CatalogoServiceAdapter(),
        perfiles=IdentidadPerfilAdapter(),
        notificador=NotificacionesAdapter(),
        uow=DjangoUnitOfWork(),
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
