"""
Serializers del contexto Identidad.

Responsabilidad estricta: validar *forma* (tipos, longitudes, obligatoriedad) y
formatear la salida. Las reglas de negocio (correo duplicado, permisos, estados)
son de los servicios; aqui no se consulta la base de datos ni se decide nada.
"""
from rest_framework import serializers

from apps.identidad.domain.models import InteresUsuario, Organizador, Usuario


# ------------------------------------------------------------------ Entrada
class RegistrarUsuarioSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    correo = serializers.EmailField()


class ConvertirEnOrganizadorSerializer(serializers.Serializer):
    nombre_comercial = serializers.CharField(max_length=200)
    cuenta_bancaria = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )


class VerificarOrganizadorSerializer(serializers.Serializer):
    aprobado = serializers.BooleanField()


class VincularInteresSerializer(serializers.Serializer):
    id_categoria = serializers.UUIDField()
    nivel_afinidad = serializers.IntegerField(
        min_value=1, max_value=5, required=False, default=3
    )


# ------------------------------------------------------------------- Salida
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "correo", "tipo_perfil", "activo", "creado_en"]
        read_only_fields = fields


class OrganizadorSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Organizador
        fields = [
            "id",
            "usuario",
            "nombre_comercial",
            "estado_verificacion",
            "calificacion_promedio",
            "creado_en",
        ]
        read_only_fields = fields


class InteresUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteresUsuario
        fields = ["id", "categoria_id", "nivel_afinidad"]
        read_only_fields = fields
