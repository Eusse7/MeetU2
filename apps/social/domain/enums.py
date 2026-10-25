from django.db import models


class EstadoResena(models.TextChoices):
    PUBLICADA = "PUBLICADA", "Publicada"
    OCULTA = "OCULTA", "Oculta"
