# reservas/urls.py
from django.urls import path
from reservas.views import CrearReservaView

urlpatterns = [
    path('reservas/crear/', CrearReservaView.as_view(), name='crear_reserva'),
]