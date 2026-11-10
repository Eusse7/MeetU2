"""
Modelos para el contexto acotado de Integraciones.
Persistencia de transacciones y vouchers de la red hotelera aliada.
"""
from django.core.validators import MinValueValidator
from django.db import models

from apps.shared.domain.base_models import BaseEntity


class ReservaHotel(BaseEntity):
    """
    Reserva confirmada en la Red Hotelera Aliada (HotelHub).
    Vincula al usuario de MeetU2 con el voucher emitido por el servicio de hoteles.
    """
    usuario_id = models.UUIDField(db_index=True, null=True, blank=True)
    codigo_reserva = models.CharField(max_length=20, unique=True, db_index=True)
    hotel_id = models.CharField(max_length=60, db_index=True)
    nombre_hotel = models.CharField(max_length=200)
    tipo_alojamiento = models.CharField(max_length=120, default="Hospedaje")
    ciudad = models.CharField(max_length=100, default="Medellín")
    fecha_checkin = models.DateField()
    fecha_checkout = models.DateField()
    habitaciones = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    noches = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_noche = models.DecimalField(max_digits=12, decimal_places=2)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    huesped_nombre = models.CharField(max_length=150)
    huesped_correo = models.EmailField()
    estado = models.CharField(max_length=20, default="CONFIRMADA", db_index=True)
    imagen_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "integraciones_reserva_hotel"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["usuario_id", "estado"], name="hotel_res_user_estado_idx"),
            models.Index(fields=["codigo_reserva"], name="hotel_res_codigo_idx"),
        ]

    def __str__(self) -> str:
        return f"Hotel {self.nombre_hotel} - {self.codigo_reserva} ({self.estado})"

