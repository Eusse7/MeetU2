"""
Rutas del contexto Identidad.

Todas cuelgan de /api/v1/identidad/, un prefijo por contexto acotado. Esa es la
unidad que un API Gateway enrutaria hacia un servicio independiente el dia que
el modulo se extraiga (ver Wiki: estrategia de Gateway).
"""
from django.urls import path

from apps.identidad.api.views import (
    ConvertirEnOrganizadorView,
    InteresesUsuarioView,
    InteresUsuarioDetailView,
    OrganizadorDetailView,
    OrganizadorDeUsuarioView,
    UsuarioDetailView,
    UsuarioListCreateView,
    UsuarioPorCorreoView,
    VerificarOrganizadorView,
)

app_name = "identidad"

urlpatterns = [
    path("usuarios", UsuarioListCreateView.as_view(), name="usuario-crear"),
    path("usuarios/buscar", UsuarioPorCorreoView.as_view(), name="usuario-buscar"),
    path(
        "usuarios/<uuid:id_usuario>",
        UsuarioDetailView.as_view(),
        name="usuario-detalle",
    ),
    path(
        "usuarios/<uuid:id_usuario>/organizador",
        ConvertirEnOrganizadorView.as_view(),
        name="convertir-organizador",
    ),
    path(
        "usuarios/<uuid:id_usuario>/perfil-organizador",
        OrganizadorDeUsuarioView.as_view(),
        name="organizador-de-usuario",
    ),
    path(
        "usuarios/<uuid:id_usuario>/intereses",
        InteresesUsuarioView.as_view(),
        name="intereses-usuario",
    ),
    path(
        "usuarios/<uuid:id_usuario>/intereses/<uuid:id_categoria>",
        InteresUsuarioDetailView.as_view(),
        name="interes-detalle",
    ),
    path(
        "organizadores/<uuid:id_organizador>",
        OrganizadorDetailView.as_view(),
        name="organizador-detalle",
    ),
    path(
        "organizadores/<uuid:id_organizador>/verificacion",
        VerificarOrganizadorView.as_view(),
        name="verificar-organizador",
    ),
]
