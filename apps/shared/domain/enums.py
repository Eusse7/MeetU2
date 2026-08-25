from django.db import models

class TipoPerfil(models.TextChoices):
    ASISTENTE = "ASISTENTE", "Asistente"
    ORGANIZADOR = "ORGANIZADOR", "Organizador"


class EstadoValidacion(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    VERIFICADO = "VERIFICADO", "Verificado"
    RECHAZADO = "RECHAZADO", "Rechazado"


class MetodoPago(models.TextChoices):
    TARJETA = "TARJETA", "Tarjeta"
    PSE = "PSE", "PSE"
    EFECTIVO = "EFECTIVO", "Efectivo"