# apps/identidad/domain/models.py
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

    @property
    def es_organizador(self) -> bool:
        return hasattr(self, "perfil_organizador")


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

    @property
    def puede_publicar(self) -> bool:
        return self.estado_verificacion == EstadoValidacion.VERIFICADO
