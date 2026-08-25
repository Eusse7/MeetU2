"""
Capa de presentacion del contexto Catalogo.

Validar -> delegar en el caso de uso -> responder. Ninguna vista calcula
precios, comprueba aforos ni consulta el ORM.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogo import container
from apps.catalogo.api.serializers import (
    CancelarExperienciaSerializer,
    CategoriaInteresSerializer,
    CrearCategoriaSerializer,
    CrearUbicacionSerializer,
    ExperienciaRecomendadaSerializer,
    ExperienciaSerializer,
    FiltroExperienciasSerializer,
    PublicarExperienciaSerializer,
    UbicacionSerializer,
)
from apps.catalogo.application.dtos import (
    CrearCategoriaDTO,
    CrearUbicacionDTO,
    FiltroExperienciasDTO,
    PublicarExperienciaDTO,
)


def _filtro_desde_query(request) -> FiltroExperienciasDTO:
    """Traduce query params a un DTO. Es adaptacion de transporte, no negocio."""
    datos = {
        clave: valor
        for clave, valor in request.query_params.items()
        if valor not in ("", None) and clave != "categorias"
    }
    categorias = request.query_params.getlist("categorias")
    if categorias:
        datos["categorias"] = categorias

    entrada = FiltroExperienciasSerializer(data=datos)
    entrada.is_valid(raise_exception=True)
    validado = entrada.validated_data
    return FiltroExperienciasDTO(
        texto=validado["texto"],
        ciudad=validado["ciudad"],
        categorias=tuple(validado["categorias"]),
        fecha_desde=validado["fecha_desde"],
        fecha_hasta=validado["fecha_hasta"],
        precio_maximo=validado["precio_maximo"],
        solo_con_cupo=validado["solo_con_cupo"],
    )


class UbicacionListCreateView(APIView):
    """GET/POST /ubicaciones"""

    def get(self, request):
        ubicaciones = container.listar_ubicaciones().ejecutar()
        return Response(UbicacionSerializer(ubicaciones, many=True).data)

    def post(self, request):
        entrada = CrearUbicacionSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        ubicacion = container.crear_ubicacion().ejecutar(
            CrearUbicacionDTO(**entrada.validated_data)
        )
        return Response(
            UbicacionSerializer(ubicacion).data, status=status.HTTP_201_CREATED
        )


class CategoriaListCreateView(APIView):
    """GET/POST /categorias"""

    def get(self, request):
        categorias = container.listar_categorias().ejecutar()
        return Response(CategoriaInteresSerializer(categorias, many=True).data)

    def post(self, request):
        entrada = CrearCategoriaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        categoria = container.crear_categoria().ejecutar(
            CrearCategoriaDTO(**entrada.validated_data)
        )
        return Response(
            CategoriaInteresSerializer(categoria).data, status=status.HTTP_201_CREATED
        )


class ExperienciaListCreateView(APIView):
    """GET /experiencias (descubrir)  ·  POST /experiencias (publicar)."""

    def get(self, request):
        experiencias = container.buscar_experiencias().ejecutar(
            _filtro_desde_query(request)
        )
        return Response(ExperienciaSerializer(experiencias, many=True).data)

    def post(self, request):
        entrada = PublicarExperienciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        validado = dict(entrada.validated_data)
        validado["categorias"] = tuple(validado.pop("categorias", ()))

        experiencia = container.publicar_experiencia().ejecutar(
            PublicarExperienciaDTO(**validado)
        )
        return Response(
            ExperienciaSerializer(experiencia).data, status=status.HTTP_201_CREATED
        )


class ExperienciaDetailView(APIView):
    """GET /experiencias/{id}"""

    def get(self, request, id_experiencia):
        experiencia = container.obtener_experiencia().ejecutar(id_experiencia)
        return Response(ExperienciaSerializer(experiencia).data)


class CancelarExperienciaView(APIView):
    """POST /experiencias/{id}/cancelacion"""

    def post(self, request, id_experiencia):
        entrada = CancelarExperienciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        experiencia = container.cancelar_experiencia().ejecutar(
            id_experiencia,
            entrada.validated_data["id_organizador"],
            entrada.validated_data["motivo"],
        )
        return Response(ExperienciaSerializer(experiencia).data)


class ExperienciasDeOrganizadorView(APIView):
    """GET /organizadores/{id}/experiencias"""

    def get(self, request, id_organizador):
        experiencias = container.listar_experiencias_organizador().ejecutar(
            id_organizador
        )
        return Response(ExperienciaSerializer(experiencias, many=True).data)


class ExperienciasRecomendadasView(APIView):
    """GET /usuarios/{id}/recomendaciones -- catalogo ordenado por afinidad."""

    def get(self, request, id_usuario):
        recomendadas = container.recomendar_experiencias().ejecutar(
            id_usuario, _filtro_desde_query(request)
        )
        return Response(ExperienciaRecomendadaSerializer(recomendadas, many=True).data)
