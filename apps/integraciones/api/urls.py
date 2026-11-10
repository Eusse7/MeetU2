from django.urls import path

from apps.integraciones.api.views import (
    CancelarReservaHotelAPIView,
    ClimaAPIView,
    DetalleReporteAsincronoAPIView,
    ExperienciasPublicasAPIView,
    MisReservasHotelAPIView,
    PartnerHotelesAPIView,
    PlanesAliadosAPIView,
    ReporteAsincronoAPIView,
    ReservarHotelAliadoAPIView,
    SimuladorHotelesAPIView,
)

app_name = "integraciones"

urlpatterns = [
    # Servicio a Proveer (endpoint JSON con información relevante del sistema)
    path(
        "experiencias-publicas/",
        ExperienciasPublicasAPIView.as_view(),
        name="experiencias_publicas",
    ),
    # Servicio a Consumir (consumo de la API del equipo aliado - Hoteles)
    path(
        "aliados/planes/",
        PlanesAliadosAPIView.as_view(),
        name="planes_aliados",
    ),
    path(
        "aliados/hoteles/",
        PlanesAliadosAPIView.as_view(),
        name="hoteles_aliados",
    ),
    # API Externa del Equipo Aliado (Red Hotelera Aliada - HotelHub)
    path(
        "partner/hotels/",
        PartnerHotelesAPIView.as_view(),
        name="partner_hotels",
    ),
    # Alias para compatibilidad
    path(
        "simulador/hoteles/",
        SimuladorHotelesAPIView.as_view(),
        name="simulador_hoteles",
    ),
    # Reserva y gestión en el Servicio de Hoteles Aliado
    path(
        "aliados/hoteles/reserva/",
        ReservarHotelAliadoAPIView.as_view(),
        name="reservar_hotel_aliado",
    ),
    path(
        "aliados/hoteles/mis-reservas/",
        MisReservasHotelAPIView.as_view(),
        name="mis_reservas_hotel",
    ),
    path(
        "aliados/hoteles/reservas/<str:codigo_reserva>/cancelar/",
        CancelarReservaHotelAPIView.as_view(),
        name="cancelar_reserva_hotel",
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
