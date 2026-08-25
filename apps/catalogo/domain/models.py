"""
Entidades del contexto Catalogo.

Los modelos son estructura + integridad de datos (tipos, validadores y
constraints de base de datos). Las reglas de negocio viven en
`domain/policies.py` y la orquestacion en `application/services.py`.
"""
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.catalogo.domain.enums import EstadoExperiencia, Modalidad
from apps.shared.domain.base_models import BaseEntity


class CategoriaInteres(BaseEntity):
    """Taxonomia compartida: clasifica experiencias y perfila usuarios."""

    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "catalogo_categoria_interes"
        ordering = ["nombre"]
        verbose_name = "categoria de interes"
        verbose_name_plural = "categorias de interes"

    def __str__(self) -> str:
        return self.nombre

    def save(self, *args, **kwargs):
        # Derivacion de un campo de persistencia, no una regla de negocio.
        if not self.slug:
            self.slug = slugify(self.nombre)[:90]
        return super().save(*args, **kwargs)


class Ubicacion(BaseEntity):
    """Sitio fisico donde ocurre una experiencia."""

    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    latitud = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]
    )
    longitud = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )
    aforo_maximo = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "catalogo_ubicacion"
        ordering = ["ciudad", "nombre"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(aforo_maximo__gte=1),
                name="ubicacion_aforo_positivo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.ciudad})"


class Experiencia(BaseEntity):
    """
    Entidad central del catalogo y la mas compleja del sistema: agrega
    organizador, ubicacion, agenda, precio, aforo y clasificacion. Por eso su
    construccion se delega a `ExperienciaBuilder`.
    """

    # Referencia por identificador al contexto Identidad: no hay ForeignKey
    # cruzada entre contextos para que cada modulo pueda extraerse a un
    # servicio independiente sin romper el esquema (ver Wiki: Strangler).
    organizador_id = models.UUIDField(db_index=True)

    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(max_length=2000, blank=True)
    modalidad = models.CharField(
        max_length=20, choices=Modalidad.choices, default=Modalidad.PRESENCIAL
    )
    fecha_hora = models.DateTimeField(db_index=True)
    duracion_minutos = models.PositiveIntegerField(
        default=120, validators=[MinValueValidator(15)]
    )
    precio = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    cupo_maximo = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    cupo_disponible = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoExperiencia.choices,
        default=EstadoExperiencia.BORRADOR,
        db_index=True,
    )
    ubicacion = models.ForeignKey(
        Ubicacion, on_delete=models.PROTECT, related_name="experiencias"
    )
    categorias = models.ManyToManyField(
        CategoriaInteres, related_name="experiencias", blank=True
    )
    motivo_cancelacion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "catalogo_experiencia"
        ordering = ["fecha_hora"]
        indexes = [
            models.Index(fields=["estado", "fecha_hora"], name="exp_estado_fecha_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cupo_disponible__lte=models.F("cupo_maximo")),
                name="experiencia_cupo_disponible_coherente",
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gte=0),
                name="experiencia_precio_no_negativo",
            ),
        ]

    def __str__(self) -> str:
        return self.titulo
