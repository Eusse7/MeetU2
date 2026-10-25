from django.urls import path

from apps.integraciones.api.views import (
    ClimaAPIView,
    DetalleReporteAsincronoAPIView,
    ExperienciasPublicasAPIView,
    PlanesAliadosAPIView,
    ReporteAsincronoAPIView,
)

app_name = "integraciones"

urlpatterns = [
    # Servicio a Proveer (endpoint JSON con información relevante del sistema)
    path(
        "experiencias-publicas/",
        ExperienciasPublicasAPIView.as_view(),
        name="experiencias_publicas",
    ),
    # Servicio a Consumir (consumo de la API del equipo aliado)
    path(
        "aliados/planes/",
        PlanesAliadosAPIView.as_view(),
        name="planes_aliados",
    ),
    # API de Terceros vía Patrón Adapter e Inversión de Dependencias (Open-Meteo)
    path(
        "clima/",
        ClimaAPIView.as_view(),
        name="clima",
    ),
    # Comunicación Asíncrona con Message Broker (Redis/Celery)
    path(
        "reportes/asincrono/",
        ReporteAsincronoAPIView.as_view(),
        name="solicitar_reporte",
    ),
    path(
        "reportes/asincrono/<str:task_id>/",
        DetalleReporteAsincronoAPIView.as_view(),
        name="detalle_reporte",
    ),
]
