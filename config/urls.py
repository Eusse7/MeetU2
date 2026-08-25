"""
Enrutado raiz.

Cada contexto acotado se monta bajo /api/v1/<contexto>/. Ese prefijo es la
unidad de enrutamiento que un API Gateway usaria para dirigir el trafico a un
servicio independiente cuando el modulo se extraiga del monolito, sin que
cambie ni una URL para los clientes (ver docs/wiki/03-api-gateway.md).
"""
from django.contrib import admin
from django.urls import include, path

from apps.shared.api.health import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", HealthView.as_view(), name="health"),
    path("api/v1/identidad/", include("apps.identidad.api.urls")),
    path("api/v1/catalogo/", include("apps.catalogo.api.urls")),
    path("api/v1/reservas/", include("apps.reservas.api.urls")),
    # El front va de ultimo: captura la raiz sin ensombrecer la API.
    path("", include("apps.frontend.urls")),
]
