from django.db import models


class EstadoReserva(models.TextChoices):
    """Ciclo de vida de una reserva, de la solicitud al check-in."""

    PENDIENTE_PAGO = "PENDIENTE_PAGO", "Pendiente de pago"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    CHECK_IN = "CHECK_IN", "Check-in realizado"
    CANCELADA = "CANCELADA", "Cancelada"
    EXPIRADA = "EXPIRADA", "Expirada"
    NO_ASISTIO = "NO_ASISTIO", "No asistio"


class OrigenCancelacion(models.TextChoices):
    USUARIO = "USUARIO", "Usuario"
    ORGANIZADOR = "ORGANIZADOR", "Organizador"
    SISTEMA = "SISTEMA", "Sistema"
