from django.db import models
from catalogo.models import Experiencia

class Reserva(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Confirmada', 'Confirmada'),
        ('Cancelada', 'Cancelada')
    ]
    
    # Relación entre módulos: Foreign Key apuntando a la app Catalogo
    experiencia = models.ForeignKey(Experiencia, on_delete=models.CASCADE, related_name='reservas')
    cantidad_personas = models.IntegerField()
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')

    def __str__(self):
        return f"Reserva {self.id} - {self.estado}"