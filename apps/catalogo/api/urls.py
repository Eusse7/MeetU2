"""Rutas del contexto Catalogo (prefijo /api/v1/catalogo/)."""
from django.urls import path

from apps.catalogo.api.views import (
    CancelarExperienciaView,
    CategoriaListCreateView,
    ExperienciaDetailView,
    ExperienciaListCreateView,
    ExperienciasDeOrganizadorView,
    ExperienciasRecomendadasView,
    UbicacionListCreateView,
)

app_name = "catalogo"

urlpatterns = [
    path("experiencias", ExperienciaListCreateView.as_view(), name="experiencia-lista"),
    path(
        "experiencias/<uuid:id_experiencia>",
        ExperienciaDetailView.as_view(),
        name="experiencia-detalle",
    ),
    path(
        "experiencias/<uuid:id_experiencia>/cancelacion",
        CancelarExperienciaView.as_view(),
        name="experiencia-cancelar",
    ),
    path(
        "organizadores/<uuid:id_organizador>/experiencias",
        ExperienciasDeOrganizadorView.as_view(),
        name="experiencias-organizador",
    ),
    path(
        "usuarios/<uuid:id_usuario>/recomendaciones",
        ExperienciasRecomendadasView.as_view(),
        name="experiencias-recomendadas",
    ),
    path("ubicaciones", UbicacionListCreateView.as_view(), name="ubicacion-lista"),
    path("categorias", CategoriaListCreateView.as_view(), name="categoria-lista"),
]
