from django.contrib import admin
from django.urls import path
from reservas.views import CrearReservaView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('reservas/crear/', CrearReservaView.as_view(), name='crear_reserva'),
]