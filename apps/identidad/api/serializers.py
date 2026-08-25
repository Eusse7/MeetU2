from rest_framework import serializers

from apps.identidad.domain.models import Organizador, Usuario


class RegistrarUsuarioSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    correo = serializers.EmailField()


class ConvertirEnOrganizadorSerializer(serializers.Serializer):
    nombre_comercial = serializers.CharField(max_length=200)
    cuenta_bancaria = serializers.CharField(max_length=64, required=False, default="")


class VerificarOrganizadorSerializer(serializers.Serializer):
    aprobado = serializers.BooleanField()


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "correo", "tipo_perfil", "activo", "creado_en"]


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
        ]