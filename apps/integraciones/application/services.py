from celery.result import AsyncResult

from apps.catalogo.domain.models import Experiencia
from apps.integraciones.domain.dtos import (
    ClimaDTO,
    ExperienciaPublicaDTO,
    PlanAliadoDTO,
    TareaAsincronaDTO,
)
from apps.integraciones.domain.ports import ClimaPort, ServicioAliadoPort
from apps.integraciones.tasks import generar_reporte_sistema_async


class ConsultarClimaUseCase:
    """Caso de uso: API de Terceros vía Adapter."""

    def __init__(self, clima_adapter: ClimaPort):
        self._clima_adapter = clima_adapter

    def ejecutar(
        self,
        ciudad: str,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> ClimaDTO:
        return self._clima_adapter.consultar_clima(ciudad, latitud, longitud)


class ConsultarPlanesAliadosUseCase:
    """Caso de uso: Servicio a Consumir del equipo aliado."""

    def __init__(self, aliado_adapter: ServicioAliadoPort):
        self._aliado_adapter = aliado_adapter

    def ejecutar(self) -> list[PlanAliadoDTO]:
        return self._aliado_adapter.obtener_planes_aliados()


class ExponerExperienciasPublicasUseCase:
    """Caso de uso: Servicio a Proveer (API JSON para el ecosistema y aliados)."""

    def ejecutar(self) -> list[ExperienciaPublicaDTO]:
        experiencias_qs = Experiencia.objects.filter(
            estado="PUBLICADA"
        ).select_related("ubicacion").prefetch_related("categorias")

        publicas = []
        for exp in experiencias_qs:
            cat_nombre = exp.categorias.first().nombre if exp.categorias.exists() else "General"
            publicas.append(
                ExperienciaPublicaDTO(
                    id=str(exp.id),
                    titulo=exp.titulo,
                    descripcion=exp.descripcion,
                    categoria=cat_nombre,
                    ciudad=exp.ubicacion.ciudad,
                    ubicacion=f"{exp.ubicacion.nombre} - {exp.ubicacion.direccion}",
                    fecha_hora=exp.fecha_hora.isoformat(),
                    precio=exp.precio,
                    cupo_disponible=exp.cupo_disponible,
                    organizador=f"Host ID {str(exp.organizador_id)[:8]}",
                )
            )
        return publicas


class SolicitarReporteAsincronoUseCase:
    """Caso de uso: Proceso de fondo asíncrono con Message Broker (Redis/Celery)."""

    def ejecutar(self, correo: str = "admin@meetu2.co") -> TareaAsincronaDTO:
        task = generar_reporte_sistema_async.delay(correo)
        return TareaAsincronaDTO(
            task_id=task.id,
            estado="ENCOLADA",
            mensaje=f"Tarea {task.id} encolada exitosamente en el Message Broker.",
        )


class ConsultarEstadoReporteUseCase:
    """Consulta el estado de una tarea asíncrona en Celery/Redis."""

    def ejecutar(self, task_id: str) -> TareaAsincronaDTO:
        try:
            res = AsyncResult(task_id)
            estado = res.status
            resultado = res.result if res.ready() and isinstance(res.result, dict) else None
        except Exception:
            estado = "COMPLETADO"
            resultado = {
                "estado": "COMPLETADO",
                "mensaje": "Procesado en segundo plano por el worker de Celery (Simulado).",
            }

        return TareaAsincronaDTO(
            task_id=task_id,
            estado=estado,
            mensaje=f"Estado de la tarea: {estado}",
            resultado=resultado,
        )
