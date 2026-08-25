"""
Capa de presentacion del contexto Identidad.

Cada vista hace exactamente tres cosas: validar la forma de la peticion con un
serializer, delegar en un caso de uso y traducir el resultado a HTTP. No hay
calculos, ni consultas al ORM, ni condicionales de negocio: los errores de
dominio suben y `domain_exception_handler` los convierte en 400/404/409.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identidad import container
from apps.identidad.api.serializers import (
    ConvertirEnOrganizadorSerializer,
    InteresUsuarioSerializer,
    OrganizadorSerializer,
    RegistrarUsuarioSerializer,
    UsuarioSerializer,
    VerificarOrganizadorSerializer,
    VincularInteresSerializer,
)
from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
    VincularInteresDTO,
)


class UsuarioListCreateView(APIView):
    """POST /usuarios -> registra un asistente."""

    def post(self, request):
        entrada = RegistrarUsuarioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)  # 400

        usuario = container.registrar_usuario().ejecutar(
            RegistrarUsuarioDTO(**entrada.validated_data)
        )
        return Response(
            UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED
        )


class UsuarioDetailView(APIView):
    """GET /usuarios/{id}"""

    def get(self, request, id_usuario):
        usuario = container.obtener_usuario().ejecutar(id_usuario)  # 404
        return Response(UsuarioSerializer(usuario).data)


class UsuarioPorCorreoView(APIView):
    """GET /usuarios/buscar?correo=... -- sesion provisional del front."""

    def get(self, request):
        correo = request.query_params.get("correo", "")
        usuario = container.buscar_usuario_por_correo().ejecutar(correo)
        return Response(UsuarioSerializer(usuario).data)


class ConvertirEnOrganizadorView(APIView):
    """POST /usuarios/{id}/organizador"""

    def post(self, request, id_usuario):
        entrada = ConvertirEnOrganizadorSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        organizador = container.convertir_en_organizador().ejecutar(
            ConvertirEnOrganizadorDTO(id_usuario=id_usuario, **entrada.validated_data)
        )
        return Response(
            OrganizadorSerializer(organizador).data, status=status.HTTP_201_CREATED
        )


class OrganizadorDeUsuarioView(APIView):
    """GET /usuarios/{id}/organizador"""

    def get(self, request, id_usuario):
        organizador = container.obtener_organizador_de_usuario().ejecutar(id_usuario)
        if organizador is None:
            return Response({"organizador": None})
        return Response(OrganizadorSerializer(organizador).data)


class OrganizadorDetailView(APIView):
    """GET /organizadores/{id}"""

    def get(self, request, id_organizador):
        organizador = container.obtener_organizador().ejecutar(id_organizador)
        return Response(OrganizadorSerializer(organizador).data)


class VerificarOrganizadorView(APIView):
    """PATCH /organizadores/{id}/verificacion -- backoffice."""

    def patch(self, request, id_organizador):
        entrada = VerificarOrganizadorSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        organizador = container.verificar_organizador().ejecutar(
            id_organizador, entrada.validated_data["aprobado"]
        )
        return Response(OrganizadorSerializer(organizador).data)


class InteresesUsuarioView(APIView):
    """GET/POST /usuarios/{id}/intereses"""

    def get(self, request, id_usuario):
        intereses = container.listar_intereses().ejecutar(id_usuario)
        return Response(InteresUsuarioSerializer(intereses, many=True).data)

    def post(self, request, id_usuario):
        entrada = VincularInteresSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        interes = container.vincular_interes().ejecutar(
            VincularInteresDTO(id_usuario=id_usuario, **entrada.validated_data)
        )
        return Response(
            InteresUsuarioSerializer(interes).data, status=status.HTTP_201_CREATED
        )


class InteresUsuarioDetailView(APIView):
    """DELETE /usuarios/{id}/intereses/{id_categoria}"""

    def delete(self, request, id_usuario, id_categoria):
        container.desvincular_interes().ejecutar(id_usuario, id_categoria)
        return Response(status=status.HTTP_204_NO_CONTENT)
