from django.contrib import admin
from django.urls import include, path

from apps.shared.api.health import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", HealthView.as_view()),
    path("api/v1/identidad/", include("apps.identidad.api.urls")),
    #path("api/v1/catalogo/", include("apps.catalogo.api.urls")),
    path("", include("apps.frontend.urls")),   # va de último
]