"""
Entidades del contexto Social.

Modela la interaccion social posterior al evento: la entidad central es
`Resena`, que vincula una reserva con asistencia comprobada a una valoracion
numerica (1 a 5 estrellas) y un comentario opcional.
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.shared.domain.base_models import BaseEntity
from apps.social.domain.enums import EstadoResena


class Resena(BaseEntity):
    """
    Reseña dejada por un asistente sobre una experiencia completada.

    Mantiene referencias por UUID a Reservas, Identidad y Catalogo para
    preservar la independencia del modulo y facilitar su extraccion.
    """

    reserva_id = models.UUIDField(unique=True, db_index=True)
    usuario_id = models.UUIDField(db_index=True)
    experiencia_id = models.UUIDField(db_index=True)
    organizador_id = models.UUIDField(db_index=True)

    calificacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(max_length=1000, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoResena.choices,
        default=EstadoResena.PUBLICADA,
        db_index=True,
    )

    class Meta:
        db_table = "social_resena"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["organizador_id", "estado"], name="resena_org_estado_idx"),
            models.Index(fields=["experiencia_id", "estado"], name="resena_exp_estado_idx"),
            models.Index(fields=["usuario_id", "estado"], name="resena_usu_estado_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(calificacion__gte=1, calificacion__lte=5),
                name="social_resena_calificacion_en_rango",
            ),
        ]

    def __str__(self) -> str:
        return f"Resena {self.calificacion}★ (reserva {self.reserva_id})"
