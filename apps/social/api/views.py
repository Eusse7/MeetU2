"""
Capa de presentacion del contexto Social.

Endpoints:
  POST /api/v1/social/resenas                          -> publicar reseña
  GET  /api/v1/social/resenas?usuario_id=...           -> listar reseñas por usuario
  GET  /api/v1/social/resenas/{id}                     -> obtener detalle de reseña
  GET  /api/v1/social/reservas/{id}/resena             -> reseña de una reserva
  GET  /api/v1/social/experiencias/{id}/resenas        -> listar reseñas de una experiencia
  GET  /api/v1/social/experiencias/{id}/metricas       -> promedio y total de experiencia
  GET  /api/v1/social/organizadores/{id}/resenas       -> listar reseñas de un organizador
  GET  /api/v1/social/organizadores/{id}/metricas      -> promedio, total y desglose de organizador
"""
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.social import container
from apps.social.api.serializers import (
    CrearResenaSerializer,
    MetricasExperienciaSerializer,
    MetricasOrganizadorSerializer,
    ResenaSerializer,
)
from apps.social.application.dtos import CrearResenaDTO
from apps.social.domain.exceptions import ResenaNoEncontrada


class ResenaListCreateView(APIView):
    def post(self, request):
        entrada = CrearResenaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        resena = container.crear_resena().ejecutar(
            CrearResenaDTO(**entrada.validated_data)
        )
        return Response(ResenaSerializer(resena).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        id_usuario = request.query_params.get("usuario_id")
        if id_usuario:
            resenas = container.listar_resenas_usuario().ejecutar(UUID(id_usuario))
        else:
            resenas = container.listar_resenas_recientes().ejecutar()
        return Response(ResenaSerializer(resenas, many=True).data)


class ResenaDetailView(APIView):
    def get(self, request, id_resena: UUID):
        resena = container.obtener_resena().ejecutar(id_resena)
        return Response(ResenaSerializer(resena).data)


class ResenaReservaView(APIView):
    def get(self, request, id_reserva: UUID):
        resena = container.obtener_resena_de_reserva().ejecutar(id_reserva)
        if resena is None:
            raise ResenaNoEncontrada(f"No existe reseña para la reserva {id_reserva}")
        return Response(ResenaSerializer(resena).data)


class ExperienciaResenasView(APIView):
    def get(self, request, id_experiencia: UUID):
        resenas = container.listar_resenas_experiencia().ejecutar(id_experiencia)
        return Response(ResenaSerializer(resenas, many=True).data)


class ExperienciaMetricasView(APIView):
    def get(self, request, id_experiencia: UUID):
        metricas = container.obtener_metricas_experiencia().ejecutar(id_experiencia)
        return Response(MetricasExperienciaSerializer(metricas).data)


class OrganizadorResenasView(APIView):
    def get(self, request, id_organizador: UUID):
        resenas = container.listar_resenas_organizador().ejecutar(id_organizador)
        return Response(ResenaSerializer(resenas, many=True).data)


class OrganizadorMetricasView(APIView):
    def get(self, request, id_organizador: UUID):
        metricas = container.obtener_metricas_organizador().ejecutar(id_organizador)
        return Response(MetricasOrganizadorSerializer(metricas).data)
