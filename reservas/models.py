# reservas/models.py
from django.db import models
from django.contrib.auth.models import User

class Experiencia(models.Model):
    titulo = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    cupo_disponible = models.IntegerField()
    estado = models.CharField(max_length=20, default='abierta')

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    experiencia = models.ForeignKey(Experiencia, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, default='pendiente')
    cantidad_cupos = models.IntegerField(default=1)
    precio_final = models.DecimalField(max_digits=8, decimal_places=2)
    fecha_reserva = models.DateTimeField(auto_now_add=True)