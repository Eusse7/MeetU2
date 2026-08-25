from django.urls import path

from apps.identidad.api.views import (
    ConvertirEnOrganizadorView,
    UsuarioDetailView,
    UsuarioListCreateView,
    VerificarOrganizadorView,
)

app_name = "identidad"

urlpatterns = [
    path("usuarios", UsuarioListCreateView.as_view(), name="usuario-crear"),
    path("usuarios/<uuid:id_usuario>", UsuarioDetailView.as_view(), name="usuario-detalle"),
    path(
        "usuarios/<uuid:id_usuario>/organizador",
        ConvertirEnOrganizadorView.as_view(),
        name="convertir-organizador",
    ),
    path(
        "organizadores/<uuid:id_organizador>/verificacion",
        VerificarOrganizadorView.as_view(),
        name="verificar-organizador",
    ),
]