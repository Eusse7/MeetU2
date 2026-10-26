"""Dominio puro del microservicio Social."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid


class EstadoResena(str, Enum):
    PUBLICADA = "PUBLICADA"
    MODERADA = "MODERADA"
    OCULTA = "OCULTA"


@dataclass
class Resena:
    reserva_id: uuid.UUID
    usuario_id: uuid.UUID
    experiencia_id: uuid.UUID
    organizador_id: uuid.UUID
    calificacion: int
    comentario: str = ""
    estado: EstadoResena = EstadoResena.PUBLICADA
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not (1 <= self.calificacion <= 5):
            raise ValueError(f"La calificacion debe estar entre 1 y 5 estrellas, se recibio {self.calificacion}")
        if len(self.comentario) > 1000:
            raise ValueError("El comentario no puede superar los 1000 caracteres")


@dataclass
class ReputacionOrganizador:
    organizador_id: uuid.UUID
    promedio: float
    total_resenas: int
