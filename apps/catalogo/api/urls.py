from django.urls import path

from apps.catalogo.api.views import (
    ExperienciaDetailView,
    ExperienciaListCreateView,
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
    path("ubicaciones", UbicacionListCreateView.as_view(), name="ubicacion-lista"),
]