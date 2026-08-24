from django.db import models
from django.core.exceptions import ValidationError

class Experiencia(models.Model):
    titulo = models.CharField(max_length=255)
    cupos_totales = models.IntegerField()
    cupos_disponibles = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        # Validación de integridad de los datos
        if self.cupos_disponibles > self.cupos_totales:
            raise ValidationError("Los cupos disponibles no pueden superar los totales.")

    def verificar_disponibilidad(self, cantidad):
        if cantidad > self.cupos_disponibles:
            raise ValidationError("No hay suficientes cupos para esta experiencia.")
        return True

    def descontar_cupos(self, cantidad):
        self.verificar_disponibilidad(cantidad)
        self.cupos_disponibles -= cantidad
        self.save()

    def __str__(self):
        return self.titulo