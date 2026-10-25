"""DTOs del contexto Social."""
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CrearResenaDTO:
    id_reserva: UUID
    id_usuario: UUID
    calificacion: int
    comentario: str = ""


@dataclass(frozen=True)
class MetricasOrganizadorDTO:
    id_organizador: UUID
    calificacion_promedio: Decimal
    total_resenas: int
    desglose: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricasExperienciaDTO:
    id_experiencia: UUID
    calificacion_promedio: Decimal
    total_resenas: int
    desglose: dict[int, int] = field(default_factory=dict)
