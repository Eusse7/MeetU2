from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ClimaDTO:
    """Información del clima obtenida de la API externa (Tercero vía Adapter)."""
    temperatura_c: float
    descripcion: str
    icono: str
    ciudad: str
    humedad_pct: int | None
    recomendacion: str
    proveedor: str


@dataclass(frozen=True)
class PlanAliadoDTO:
    """Experiencia/plan obtenido del servicio aliado (Servicio a Consumir)."""
    id: str
    titulo: str
    categoria: str
    ciudad: str
    precio: Decimal
    organizador: str
    cupos_disponibles: int
    url_externa: str
    red_aliada: str


@dataclass(frozen=True)
class ExperienciaPublicaDTO:
    """Información que MeetU2 expone a la red de aliados (Servicio a Proveer)."""
    id: str
    titulo: str
    descripcion: str
    categoria: str
    ciudad: str
    ubicacion: str
    fecha_hora: str
    precio: Decimal
    cupo_disponible: int
    organizador: str


@dataclass(frozen=True)
class TareaAsincronaDTO:
    """Estado de una tarea de fondo en Celery/Redis."""
    task_id: str
    estado: str
    mensaje: str
    resultado: dict[str, Any] | None = None
