"""Rutas del contexto Social."""
from django.urls import path

from apps.social.api.views import (
    ExperienciaMetricasView,
    ExperienciaResenasView,
    OrganizadorMetricasView,
    OrganizadorResenasView,
    ResenaDetailView,
    ResenaListCreateView,
    ResenaReservaView,
)

urlpatterns = [
    path("resenas", ResenaListCreateView.as_view(), name="resenas-list-create"),
    path("resenas/", ResenaListCreateView.as_view(), name="resenas-list-create-slash"),
    path("resenas/<uuid:id_resena>", ResenaDetailView.as_view(), name="resena-detail"),
    path("resenas/<uuid:id_resena>/", ResenaDetailView.as_view(), name="resena-detail-slash"),
    path("reservas/<uuid:id_reserva>/resena", ResenaReservaView.as_view(), name="resena-reserva"),
    path("reservas/<uuid:id_reserva>/resena/", ResenaReservaView.as_view(), name="resena-reserva-slash"),
    path("experiencias/<uuid:id_experiencia>/resenas", ExperienciaResenasView.as_view(), name="experiencia-resenas"),
    path("experiencias/<uuid:id_experiencia>/resenas/", ExperienciaResenasView.as_view(), name="experiencia-resenas-slash"),
    path("experiencias/<uuid:id_experiencia>/metricas", ExperienciaMetricasView.as_view(), name="experiencia-metricas"),
    path("experiencias/<uuid:id_experiencia>/metricas/", ExperienciaMetricasView.as_view(), name="experiencia-metricas-slash"),
    path("organizadores/<uuid:id_organizador>/resenas", OrganizadorResenasView.as_view(), name="organizador-resenas"),
    path("organizadores/<uuid:id_organizador>/resenas/", OrganizadorResenasView.as_view(), name="organizador-resenas-slash"),
    path("organizadores/<uuid:id_organizador>/metricas", OrganizadorMetricasView.as_view(), name="organizador-metricas"),
    path("organizadores/<uuid:id_organizador>/metricas/", OrganizadorMetricasView.as_view(), name="organizador-metricas-slash"),
]
