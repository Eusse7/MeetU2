"""
Serializers del contexto Social.

Validan forma y formatean salida de calificaciones y metricas.
"""
from rest_framework import serializers

from apps.social.domain.models import Resena


class CrearResenaSerializer(serializers.Serializer):
    id_reserva = serializers.UUIDField()
    id_usuario = serializers.UUIDField()
    calificacion = serializers.IntegerField(min_value=1, max_value=5)
    comentario = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )


class ResenaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    experiencia_titulo = serializers.SerializerMethodField()

    class Meta:
        model = Resena
        fields = [
            "id",
            "reserva_id",
            "usuario_id",
            "usuario_nombre",
            "experiencia_id",
            "experiencia_titulo",
            "organizador_id",
            "calificacion",
            "comentario",
            "estado",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = fields

    def get_usuario_nombre(self, obj) -> str:
        from apps.identidad.domain.models import Usuario

        usuario = Usuario.objects.filter(pk=obj.usuario_id).first()
        return usuario.nombre if usuario else "Asistente verificado"

    def get_experiencia_titulo(self, obj) -> str:
        from apps.catalogo.domain.models import Experiencia

        exp = Experiencia.objects.filter(pk=obj.experiencia_id).first()
        return exp.titulo if exp else "Experiencia"


class MetricasOrganizadorSerializer(serializers.Serializer):
    id_organizador = serializers.UUIDField()
    calificacion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_resenas = serializers.IntegerField()
    desglose = serializers.DictField(child=serializers.IntegerField())


class MetricasExperienciaSerializer(serializers.Serializer):
    id_experiencia = serializers.UUIDField()
    calificacion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_resenas = serializers.IntegerField()
    desglose = serializers.DictField(child=serializers.IntegerField())
