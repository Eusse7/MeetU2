"""
Entidades del contexto Identidad.

Los modelos definen estructura e integridad (tipos, unicidad, constraints). Las
reglas de negocio viven en `domain/policies.py` y la orquestacion en
`application/services.py`, para no caer en Fat Models.
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.shared.domain.base_models import BaseEntity
from apps.shared.domain.enums import EstadoValidacion, TipoPerfil


class Usuario(BaseEntity):
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique=True)
    tipo_perfil = models.CharField(
        max_length=20,
        choices=TipoPerfil.choices,
        default=TipoPerfil.ASISTENTE,
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "identidad_usuario"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.nombre} <{self.correo}>"


class Organizador(BaseEntity):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil_organizador",
    )
    nombre_comercial = models.CharField(max_length=200)
    estado_verificacion = models.CharField(
        max_length=20,
        choices=EstadoValidacion.choices,
        default=EstadoValidacion.PENDIENTE,
    )
    calificacion_promedio = models.DecimalField(
        max_digits=3, decimal_places=2, default=0
    )
    cuenta_bancaria = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "identidad_organizador"

    def __str__(self) -> str:
        return self.nombre_comercial


class InteresUsuario(BaseEntity):
    """
    Vinculo Usuario <-> CategoriaInteres con el nivel de afinidad declarado.

    `categoria_id` es una referencia por identificador al contexto Catalogo:
    igual que Experiencia.organizador_id, evita una ForeignKey entre contextos
    para que los modulos sigan siendo extraibles (ver Wiki: Strangler).
    """

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="intereses"
    )
    categoria_id = models.UUIDField(db_index=True)
    nivel_afinidad = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    class Meta:
        db_table = "identidad_interes_usuario"
        ordering = ["-nivel_afinidad"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "categoria_id"],
                name="interes_unico_por_usuario",
            ),
            models.CheckConstraint(
                condition=models.Q(nivel_afinidad__gte=1, nivel_afinidad__lte=5),
                name="interes_nivel_en_rango",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.usuario_id} -> {self.categoria_id} ({self.nivel_afinidad})"
