"""
Capa de presentacion del contexto Reservas.

Codigos que emite este modulo:
  201 reserva creada · 200 operacion aplicada · 400 forma o dato invalido
  404 reserva/experiencia/ticket inexistente · 409 conflicto de estado
      (cupo insuficiente, reserva duplicada, expirada, transicion ilegal)
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reservas import container
from apps.reservas.api.serializers import (
    CancelarReservaSerializer,
    CheckInSerializer,
    ConfirmarReservaSerializer,
    ReservaDetalladaSerializer,
    ReservaSerializer,
    ResultadoCancelacionSerializer,
    SolicitarReservaSerializer,
)
from apps.reservas.application.dtos import (
    CancelarReservaDTO,
    CheckInDTO,
    ConfirmarReservaDTO,
    SolicitarReservaDTO,
)


class ReservaListCreateView(APIView):
    """POST /reservas -- solicitar una reserva."""

    def post(self, request):
        entrada = SolicitarReservaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        reserva = container.solicitar_reserva().ejecutar(
            SolicitarReservaDTO(**entrada.validated_data)
        )
        return Response(
            ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED
        )


class ReservaDetailView(APIView):
    """GET /reservas/{id}"""

    def get(self, request, id_reserva):
        reserva = container.obtener_reserva().ejecutar(id_reserva)
        return Response(ReservaSerializer(reserva).data)


class ConfirmarReservaView(APIView):
    """POST /reservas/{id}/confirmacion"""

    def post(self, request, id_reserva):
        entrada = ConfirmarReservaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        reserva = container.confirmar_reserva().ejecutar(
            ConfirmarReservaDTO(id_reserva=id_reserva, **entrada.validated_data)
        )
        return Response(ReservaSerializer(reserva).data)


class CancelarReservaView(APIView):
    """POST /reservas/{id}/cancelacion"""

    def post(self, request, id_reserva):
        entrada = CancelarReservaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        resultado = container.cancelar_reserva().ejecutar(
            CancelarReservaDTO(id_reserva=id_reserva, **entrada.validated_data)
        )
        return Response(ResultadoCancelacionSerializer(resultado).data)


class CheckInView(APIView):
    """POST /reservas/check-in -- el organizador valida un ticket."""

    def post(self, request):
        entrada = CheckInSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        reserva = container.registrar_check_in().ejecutar(
            CheckInDTO(**entrada.validated_data)
        )
        return Response(ReservaSerializer(reserva).data)


class ReservasDeUsuarioView(APIView):
    """GET /usuarios/{id}/reservas -- vista 'Mis reservas'."""

    def get(self, request, id_usuario):
        detalladas = container.listar_reservas_usuario().ejecutar(id_usuario)
        return Response(ReservaDetalladaSerializer(detalladas, many=True).data)


class ReservasDeExperienciaView(APIView):
    """GET /experiencias/{id}/reservas -- panel del organizador."""

    def get(self, request, id_experiencia):
        reservas = container.listar_reservas_experiencia().ejecutar(id_experiencia)
        return Response(ReservaSerializer(reservas, many=True).data)
