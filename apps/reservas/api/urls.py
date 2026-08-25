"""Rutas del contexto Reservas (prefijo /api/v1/reservas/)."""
from django.urls import path

from apps.reservas.api.views import (
    CancelarReservaView,
    CheckInView,
    ConfirmarReservaView,
    ReservaDetailView,
    ReservaListCreateView,
    ReservasDeExperienciaView,
    ReservasDeUsuarioView,
)

app_name = "reservas"

urlpatterns = [
    path("reservas", ReservaListCreateView.as_view(), name="reserva-crear"),
    path("reservas/check-in", CheckInView.as_view(), name="reserva-check-in"),
    path(
        "reservas/<uuid:id_reserva>",
        ReservaDetailView.as_view(),
        name="reserva-detalle",
    ),
    path(
        "reservas/<uuid:id_reserva>/confirmacion",
        ConfirmarReservaView.as_view(),
        name="reserva-confirmar",
    ),
    path(
        "reservas/<uuid:id_reserva>/cancelacion",
        CancelarReservaView.as_view(),
        name="reserva-cancelar",
    ),
    path(
        "usuarios/<uuid:id_usuario>/reservas",
        ReservasDeUsuarioView.as_view(),
        name="reservas-usuario",
    ),
    path(
        "experiencias/<uuid:id_experiencia>/reservas",
        ReservasDeExperienciaView.as_view(),
        name="reservas-experiencia",
    ),
]
