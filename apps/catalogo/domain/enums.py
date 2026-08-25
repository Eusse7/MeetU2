from django.db import models


class EstadoExperiencia(models.TextChoices):
    """Ciclo de vida de una experiencia publicable."""

    BORRADOR = "BORRADOR", "Borrador"
    PUBLICADA = "PUBLICADA", "Publicada"
    AGOTADA = "AGOTADA", "Agotada"
    CANCELADA = "CANCELADA", "Cancelada"
    FINALIZADA = "FINALIZADA", "Finalizada"


class Modalidad(models.TextChoices):
    PRESENCIAL = "PRESENCIAL", "Presencial"
    HIBRIDA = "HIBRIDA", "Hibrida"
