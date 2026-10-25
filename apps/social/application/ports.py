"""Puertos del contexto Social."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from apps.social.domain.models import Resena


@dataclass(frozen=True)
class ReservaAsistenciaVista:
    """Proyeccion minima de una Reserva requerida por Social."""

    id: UUID
    usuario_id: UUID
    experiencia_id: UUID
    organizador_id: UUID
    estado: str
    check_in_en: datetime | None


class ReservaAsistenciaPort(ABC):
    """Permite a Social consultar la evidencia de asistencia de una reserva."""

    @abstractmethod
    def obtener_asistencia(self, id_reserva: UUID) -> ReservaAsistenciaVista | None: ...


class OrganizadorCalificacionPort(ABC):
    """Permite a Social actualizar la calificacion promedio del organizador en Identidad."""

    @abstractmethod
    def actualizar_calificacion_promedio(
        self, id_organizador: UUID, calificacion_promedio: Decimal
    ) -> None: ...


class ResenaRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, resena: Resena) -> Resena: ...

    @abstractmethod
    def obtener_por_id(self, id_resena: UUID) -> Resena | None: ...

    @abstractmethod
    def obtener_por_reserva(self, id_reserva: UUID) -> Resena | None: ...

    @abstractmethod
    def listar_por_experiencia(self, id_experiencia: UUID) -> list[Resena]: ...

    @abstractmethod
    def listar_por_organizador(self, id_organizador: UUID) -> list[Resena]: ...

    @abstractmethod
    def listar_por_usuario(self, id_usuario: UUID) -> list[Resena]: ...

    @abstractmethod
    def listar_recientes(self, limite: int = 20) -> list[Resena]: ...

    @abstractmethod
    def obtener_calificaciones_organizador(self, id_organizador: UUID) -> list[int]: ...

    @abstractmethod
    def obtener_calificaciones_experiencia(self, id_experiencia: UUID) -> list[int]: ...
