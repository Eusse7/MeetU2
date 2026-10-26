"""Dominio puro del microservicio de Catalogo."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
import unicodedata
import uuid


class Modalidad(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    VIRTUAL = "VIRTUAL"


class EstadoExperiencia(str, Enum):
    BORRADOR = "BORRADOR"
    PUBLICADA = "PUBLICADA"
    CANCELADA = "CANCELADA"
    FINALIZADA = "FINALIZADA"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)


@dataclass
class Categoria:
    nombre: str
    descripcion: str = ""
    slug: str = ""
    activa: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        if not self.slug:
            self.slug = slugify(self.nombre)


@dataclass
class Ubicacion:
    nombre: str
    direccion: str
    ciudad: str
    latitud: float
    longitud: float
    aforo_maximo: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        if self.aforo_maximo < 1:
            raise ValueError("El aforo maximo debe ser al menos 1")


@dataclass
class Experiencia:
    organizador_id: uuid.UUID
    categoria_id: uuid.UUID
    ubicacion_id: uuid.UUID
    titulo: str
    descripcion: str
    precio_cop: float
    cupo_maximo: int
    cupos_disponibles: int
    fecha_evento: datetime
    modalidad: Modalidad = Modalidad.PRESENCIAL
    estado: EstadoExperiencia = EstadoExperiencia.PUBLICADA
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.precio_cop < 0:
            raise ValueError("El precio no puede ser negativo")
        if self.cupo_maximo < 1:
            raise ValueError("El cupo maximo debe ser mayor a cero")
        if self.cupos_disponibles > self.cupo_maximo:
            raise ValueError("Los cupos disponibles no pueden superar el cupo maximo")
