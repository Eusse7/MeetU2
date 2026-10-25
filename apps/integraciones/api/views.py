from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integraciones import container


class ExperienciasPublicasAPIView(APIView):
    """
    Servicio a Proveer (Entregable 2):
    Expone un endpoint JSON público con información relevante del sistema MeetU2
    para que equipos aliados y terceros puedan consumir el catálogo de experiencias.
    """

    def get(self, request: Request) -> Response:
        servicio = container.exponer_experiencias_publicas()
        publicas = servicio.ejecutar()

        return Response(
            {
                "plataforma": "MeetU2",
                "version": "2.0",
                "descripcion": "API pública de experiencias para consumo de la red aliada",
                "total": len(publicas),
                "experiencias": [
                    {
                        "id": exp.id,
                        "titulo": exp.titulo,
                        "descripcion": exp.descripcion,
                        "categoria": exp.categoria,
                        "ciudad": exp.ciudad,
                        "ubicacion": exp.ubicacion,
                        "fecha_hora": exp.fecha_hora,
                        "precio": float(exp.precio),
                        "cupo_disponible": exp.cupo_disponible,
                        "organizador": exp.organizador,
                    }
                    for exp in publicas
                ],
            },
            status=status.HTTP_200_OK,
        )


class PlanesAliadosAPIView(APIView):
    """
    Servicio a Consumir (Entregable 2):
    Consume el servicio del equipo aliado (configurado en SERVICIO_ALIADO_URL)
    mediante el patrón Adapter, con fallback de contingencia en caso de indisponibilidad.
    """

    def get(self, request: Request) -> Response:
        servicio = container.consultar_planes_aliados()
        planes = servicio.ejecutar()

        return Response(
            {
                "fuente": "Red de Aliados MeetU2",
                "total": len(planes),
                "planes": [
                    {
                        "id": p.id,
                        "titulo": p.titulo,
                        "categoria": p.categoria,
                        "ciudad": p.ciudad,
                        "precio": float(p.precio),
                        "organizador": p.organizador,
                        "cupos_disponibles": p.cupos_disponibles,
                        "url_externa": p.url_externa,
                        "red_aliada": p.red_aliada,
                    }
                    for p in planes
                ],
            },
            status=status.HTTP_200_OK,
        )


class ClimaAPIView(APIView):
    """
    API de Terceros vía Patrón Adapter e Inversión de Dependencias (Entregable 2):
    Consulta el pronóstico meteorológico para la ciudad o coordenadas de un plan,
    conectando con la API REST de Open-Meteo.
    """

    def get(self, request: Request) -> Response:
        ciudad = request.query_params.get("ciudad", "Medellin")
        lat_str = request.query_params.get("lat")
        lon_str = request.query_params.get("lon")

        lat = float(lat_str) if lat_str else None
        lon = float(lon_str) if lon_str else None

        servicio = container.consultar_clima()
        clima = servicio.ejecutar(ciudad=ciudad, latitud=lat, longitud=lon)

        return Response(
            {
                "ciudad": clima.ciudad,
                "temperatura_c": clima.temperatura_c,
                "descripcion": clima.descripcion,
                "icono": clima.icono,
                "humedad_pct": clima.humedad_pct,
                "recomendacion": clima.recomendacion,
                "proveedor": clima.proveedor,
            },
            status=status.HTTP_200_OK,
        )


class ReporteAsincronoAPIView(APIView):
    """
    Comunicación Asíncrona con Message Broker (Redis/Celery - Entregable 2):
    POST: Encola la tarea de generación de reporte en segundo plano.
    GET: Consulta el estado y resultado de una tarea en Celery.
    """

    def post(self, request: Request) -> Response:
        correo = request.data.get("correo", "admin@meetu2.co")
        servicio = container.solicitar_reporte_asincrono()
        tarea = servicio.ejecutar(correo=correo)

        return Response(
            {
                "task_id": tarea.task_id,
                "estado": tarea.estado,
                "mensaje": tarea.mensaje,
                "instruccion": f"Consulta el estado en GET /api/v1/integracion/reportes/asincrono/{tarea.task_id}/",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DetalleReporteAsincronoAPIView(APIView):
    def get(self, request: Request, task_id: str) -> Response:
        servicio = container.consultar_estado_reporte()
        tarea = servicio.ejecutar(task_id=task_id)

        return Response(
            {
                "task_id": tarea.task_id,
                "estado": tarea.estado,
                "mensaje": tarea.mensaje,
                "resultado": tarea.resultado,
            },
            status=status.HTTP_200_OK,
        )
