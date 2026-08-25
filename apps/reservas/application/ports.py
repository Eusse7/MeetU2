"""
Puertos del contexto Reservas.

Reservas es el contexto con mas dependencias externas (catalogo, identidad,
notificaciones). Todas se expresan aqui como abstracciones minimas: el servicio
declara *que* necesita, no *quien* se lo da.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from apps.reservas.domain.models import Reserva


@dataclass(frozen=True)
class ExperienciaVista:
    """
    Proyeccion de solo lectura de una Experiencia.

    Reservas nunca ve la entidad de Catalogo: recibe esta vista reducida con lo
    justo para decidir. Si Catalogo cambia sus campos internos, aqui no pasa
    nada; solo cambia su adaptador.
    """

    id: UUID
    titulo: str
    organizador_id: UUID
    fecha_hora: datetime
    precio: Decimal
    cupo_disponible: int
    estado: str
    ciudad: str = ""
    direccion: str = ""


@dataclass(frozen=True)
class UsuarioVista:
    id: UUID
    nombre: str
    correo: str
    activo: bool


class ReservaRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, reserva: Reserva) -> Reserva: ...

    @abstractmethod
    def obtener_por_id(self, id_reserva: UUID) -> Reserva | None: ...

    @abstractmethod
    def obtener_por_ticket(self, codigo_ticket: str) -> Reserva | None: ...

    @abstractmethod
    def listar_por_usuario(self, id_usuario: UUID) -> list[Reserva]: ...

    @abstractmethod
    def listar_por_experiencia(self, id_experiencia: UUID) -> list[Reserva]: ...

    @abstractmethod
    def existe_activa(self, id_usuario: UUID, id_experiencia: UUID) -> bool:
        """True si el usuario ya tiene una reserva viva sobre esa experiencia."""

    @abstractmethod
    def existe_ticket(self, codigo_ticket: str) -> bool: ...


class CatalogoPort(ABC):
    """Lo que Reservas necesita del Catalogo: consultar y mover cupo."""

    @abstractmethod
    def obtener_experiencia(self, id_experiencia: UUID) -> ExperienciaVista | None: ...

    @abstractmethod
    def bloquear_cupo(self, id_experiencia: UUID, cantidad: int) -> None:
        """Retiene cupo. Lanza el error de dominio de Catalogo si no alcanza."""

    @abstractmethod
    def liberar_cupo(self, id_experiencia: UUID, cantidad: int) -> None: ...


class PerfilUsuarioPort(ABC):
    @abstractmethod
    def obtener(self, id_usuario: UUID) -> UsuarioVista | None: ...


class NotificadorPort(ABC):
    """
    Puerto propio de Reservas hacia el modulo de notificaciones.

    Se expresa en lenguaje del negocio (`reserva_creada`, `reserva_confirmada`)
    y no en lenguaje de canal: el servicio no sabe si sale por correo o por
    push. Esa decision la toma la Factory detras del adaptador.
    """

    @abstractmethod
    def reserva_creada(self, reserva: Reserva, usuario: UsuarioVista,
                       experiencia: ExperienciaVista) -> None: ...

    @abstractmethod
    def reserva_confirmada(self, reserva: Reserva, usuario: UsuarioVista,
                           experiencia: ExperienciaVista) -> None: ...

    @abstractmethod
    def reserva_cancelada(self, reserva: Reserva, usuario: UsuarioVista,
                          reembolso: Decimal) -> None: ...
