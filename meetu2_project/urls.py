# reservas/urls.py
from django.urls import path
from reservas.views import CrearReservaView, formulario_reserva

urlpatterns = [
    path('reservas/crear/', CrearReservaView.as_view(), name='crear_reserva'),
    path('reservas/formulario/', formulario_reserva, name='formulario_reserva'),
]