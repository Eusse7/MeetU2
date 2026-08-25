from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identidad.api.serializers import (
    ConvertirEnOrganizadorSerializer,
    OrganizadorSerializer,
    RegistrarUsuarioSerializer,
    UsuarioSerializer,
    VerificarOrganizadorSerializer,
)
from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
)
from apps.identidad.application.services import (
    ConvertirEnOrganizadorService,
    RegistrarUsuarioService,
    VerificarOrganizadorService,
)
from apps.identidad.domain.exceptions import UsuarioNoEncontrado
from apps.identidad.infrastructure.repositories import (
    DjangoOrganizadorRepository,
    DjangoUsuarioRepository,
)


class UsuarioListCreateView(APIView):
    def post(self, request):
        serializer = RegistrarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)          # -> 400

        servicio = RegistrarUsuarioService(usuarios=DjangoUsuarioRepository())
        usuario = servicio.ejecutar(RegistrarUsuarioDTO(**serializer.validated_data))

        return Response(UsuarioSerializer(usuario).data, status=201)


class UsuarioDetailView(APIView):
    def get(self, request, id_usuario):
        usuario = DjangoUsuarioRepository().obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe el usuario {id_usuario}")  # -> 404
        return Response(UsuarioSerializer(usuario).data, status=200)


class ConvertirEnOrganizadorView(APIView):
    def post(self, request, id_usuario):
        serializer = ConvertirEnOrganizadorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        servicio = ConvertirEnOrganizadorService(
            usuarios=DjangoUsuarioRepository(),
            organizadores=DjangoOrganizadorRepository(),
        )
        organizador = servicio.ejecutar(
            ConvertirEnOrganizadorDTO(
                id_usuario=str(id_usuario), **serializer.validated_data
            )
        )
        return Response(OrganizadorSerializer(organizador).data, status=201)


class VerificarOrganizadorView(APIView):
    def patch(self, request, id_organizador):
        serializer = VerificarOrganizadorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        servicio = VerificarOrganizadorService(
            organizadores=DjangoOrganizadorRepository()
        )
        organizador = servicio.ejecutar(
            id_organizador, serializer.validated_data["aprobado"]
        )
        return Response(OrganizadorSerializer(organizador).data, status=200)
