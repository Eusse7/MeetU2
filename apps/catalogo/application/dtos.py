"""Objetos de transferencia: frontera entre la API y la capa de aplicacion."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CrearUbicacionDTO:
    nombre: str
    direccion: str
    ciudad: str
    latitud: float
    longitud: float
    aforo_maximo: int


@dataclass(frozen=True)
class CrearCategoriaDTO:
    nombre: str
    descripcion: str = ""


@dataclass(frozen=True)
class PublicarExperienciaDTO:
    id_organizador: UUID
    id_ubicacion: UUID
    titulo: str
    fecha_hora: datetime
    precio: Decimal
    cupo_maximo: int
    descripcion: str = ""
    duracion_minutos: int = 120
    modalidad: str = "PRESENCIAL"
    categorias: tuple[UUID, ...] = ()
    descuento_porcentaje: Decimal = Decimal("0")
    publicar_de_inmediato: bool = True


@dataclass(frozen=True)
class FiltroExperienciasDTO:
    """Criterios de busqueda del caso de uso 'Descubrir'."""

    texto: str = ""
    ciudad: str = ""
    categorias: tuple[UUID, ...] = ()
    fecha_desde: datetime | None = None
    fecha_hasta: datetime | None = None
    precio_maximo: Decimal | None = None
    solo_con_cupo: bool = True


@dataclass(frozen=True)
class ExperienciaRecomendadaDTO:
    """Experiencia enriquecida con su puntaje de afinidad."""

    experiencia: object
    afinidad: float
    categorias_en_comun: tuple[str, ...] = field(default_factory=tuple)
