"""
Entidad Reserva: el nucleo transaccional de MeetU2.

Igual que en el resto de contextos, el modelo aporta estructura e integridad;
las reglas (montos, reembolsos, transiciones, ventana de check-in) estan en
`domain/policies.py`.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.reservas.domain.enums import EstadoReserva, OrigenCancelacion
from apps.shared.domain.base_models import BaseEntity


class Reserva(BaseEntity):
    # Referencias por identificador a otros contextos acotados: no hay
    # ForeignKey hacia Identidad ni Catalogo (ver Wiki: Strangler / Gateway).
    usuario_id = models.UUIDField(db_index=True)
    experiencia_id = models.UUIDField(db_index=True)
    organizador_id = models.UUIDField(db_index=True)

    codigo_ticket = models.CharField(max_length=12, unique=True, db_index=True)
    cantidad_cupos = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    # Se congela el precio del momento de la reserva: si el host lo cambia
    # despues, no altera lo ya comprometido.
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    comision_plataforma = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_reembolsado = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    estado = models.CharField(
        max_length=20,
        choices=EstadoReserva.choices,
        default=EstadoReserva.PENDIENTE_PAGO,
        db_index=True,
    )
    vence_en = models.DateTimeField(null=True, blank=True)
    confirmada_en = models.DateTimeField(null=True, blank=True)
    check_in_en = models.DateTimeField(null=True, blank=True)
    cancelada_en = models.DateTimeField(null=True, blank=True)
    origen_cancelacion = models.CharField(
        max_length=20, choices=OrigenCancelacion.choices, blank=True
    )
    motivo_cancelacion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "reservas_reserva"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(
                fields=["usuario_id", "estado"], name="reserva_usuario_estado_idx"
            ),
            models.Index(
                fields=["experiencia_id", "estado"], name="reserva_exp_estado_idx"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad_cupos__gte=1),
                name="reserva_cantidad_positiva",
            ),
            models.CheckConstraint(
                condition=models.Q(monto_total__gte=0),
                name="reserva_monto_no_negativo",
            ),
            models.CheckConstraint(
                condition=models.Q(monto_reembolsado__lte=models.F("monto_total")),
                name="reserva_reembolso_acotado",
            ),
        ]

    def __str__(self) -> str:
        return f"Reserva {self.codigo_ticket} ({self.estado})"
