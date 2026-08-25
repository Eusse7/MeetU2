"""Serializers del contexto Reservas: forma de entrada y forma de salida."""
from rest_framework import serializers

from apps.reservas.domain.models import Reserva


# ------------------------------------------------------------------ Entrada
class SolicitarReservaSerializer(serializers.Serializer):
    id_usuario = serializers.UUIDField()
    id_experiencia = serializers.UUIDField()
    cantidad_cupos = serializers.IntegerField(min_value=1, required=False, default=1)


class ConfirmarReservaSerializer(serializers.Serializer):
    referencia_pago = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )


class CancelarReservaSerializer(serializers.Serializer):
    id_usuario = serializers.UUIDField()
    motivo = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class CheckInSerializer(serializers.Serializer):
    codigo_ticket = serializers.CharField(max_length=12)
    id_organizador = serializers.UUIDField()


# ------------------------------------------------------------------- Salida
class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = [
            "id",
            "usuario_id",
            "experiencia_id",
            "organizador_id",
            "codigo_ticket",
            "cantidad_cupos",
            "precio_unitario",
            "monto_total",
            "comision_plataforma",
            "monto_reembolsado",
            "estado",
            "vence_en",
            "confirmada_en",
            "check_in_en",
            "cancelada_en",
            "motivo_cancelacion",
            "creado_en",
        ]
        read_only_fields = fields


class ReservaDetalladaSerializer(serializers.Serializer):
    """Reserva + datos de la experiencia compuestos por el servicio."""

    reserva = ReservaSerializer(read_only=True)
    experiencia_titulo = serializers.CharField(read_only=True)
    experiencia_fecha = serializers.DateTimeField(read_only=True, allow_null=True)
    experiencia_ciudad = serializers.CharField(read_only=True)


class ResultadoCancelacionSerializer(serializers.Serializer):
    reserva = ReservaSerializer(read_only=True)
    monto_reembolsado = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    porcentaje_aplicado = serializers.DecimalField(
        max_digits=3, decimal_places=2, read_only=True
    )
