"""
Serializers del contexto Catalogo.

Solo validan forma y formatean salida. Reglas como el aforo, la antelacion
minima o el estado del organizador pertenecen a las politicas de dominio y al
`ExperienciaBuilder`, no a este archivo.
"""
from rest_framework import serializers

from apps.catalogo.domain.enums import Modalidad
from apps.catalogo.domain.models import CategoriaInteres, Experiencia, Ubicacion


# ------------------------------------------------------------------ Entrada
class CrearUbicacionSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    direccion = serializers.CharField(max_length=255)
    ciudad = serializers.CharField(max_length=100)
    latitud = serializers.FloatField(min_value=-90, max_value=90)
    longitud = serializers.FloatField(min_value=-180, max_value=180)
    aforo_maximo = serializers.IntegerField(min_value=1)


class CrearCategoriaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=80)
    descripcion = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class PublicarExperienciaSerializer(serializers.Serializer):
    id_organizador = serializers.UUIDField()
    id_ubicacion = serializers.UUIDField()
    titulo = serializers.CharField(max_length=180)
    descripcion = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )
    fecha_hora = serializers.DateTimeField()
    duracion_minutos = serializers.IntegerField(min_value=15, required=False, default=120)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    cupo_maximo = serializers.IntegerField(min_value=1)
    modalidad = serializers.ChoiceField(
        choices=Modalidad.choices, required=False, default=Modalidad.PRESENCIAL
    )
    categorias = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    descuento_porcentaje = serializers.DecimalField(
        max_digits=3, decimal_places=2, min_value=0, max_value=1,
        required=False, default=0,
    )
    publicar_de_inmediato = serializers.BooleanField(required=False, default=True)


class CancelarExperienciaSerializer(serializers.Serializer):
    id_organizador = serializers.UUIDField()
    motivo = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class FiltroExperienciasSerializer(serializers.Serializer):
    """Valida los query params de la busqueda publica."""

    texto = serializers.CharField(required=False, allow_blank=True, default="")
    ciudad = serializers.CharField(required=False, allow_blank=True, default="")
    categorias = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    fecha_desde = serializers.DateTimeField(required=False, allow_null=True, default=None)
    fecha_hasta = serializers.DateTimeField(required=False, allow_null=True, default=None)
    precio_maximo = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        required=False, allow_null=True, default=None,
    )
    solo_con_cupo = serializers.BooleanField(required=False, default=True)


# ------------------------------------------------------------------- Salida
class CategoriaInteresSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaInteres
        fields = ["id", "nombre", "slug", "descripcion"]
        read_only_fields = fields


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = [
            "id",
            "nombre",
            "direccion",
            "ciudad",
            "latitud",
            "longitud",
            "aforo_maximo",
        ]
        read_only_fields = fields


class ExperienciaSerializer(serializers.ModelSerializer):
    ubicacion = UbicacionSerializer(read_only=True)
    categorias = CategoriaInteresSerializer(many=True, read_only=True)

    class Meta:
        model = Experiencia
        fields = [
            "id",
            "organizador_id",
            "titulo",
            "descripcion",
            "modalidad",
            "fecha_hora",
            "duracion_minutos",
            "precio",
            "cupo_maximo",
            "cupo_disponible",
            "estado",
            "ubicacion",
            "categorias",
            "motivo_cancelacion",
        ]
        read_only_fields = fields


class ExperienciaRecomendadaSerializer(serializers.Serializer):
    """Envuelve la experiencia con su puntaje de afinidad."""

    experiencia = ExperienciaSerializer(read_only=True)
    afinidad = serializers.FloatField(read_only=True)
    categorias_en_comun = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
