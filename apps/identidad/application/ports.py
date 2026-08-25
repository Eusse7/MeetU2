# apps/identidad/application/ports.py
from abc import ABC, abstractmethod
from uuid import UUID

from apps.identidad.domain.models import Organizador, Usuario


class UsuarioRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def obtener_por_id(self, id_usuario: UUID) -> Usuario | None: ...

    @abstractmethod
    def existe_correo(self, correo: str) -> bool: ...


class OrganizadorRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, organizador: Organizador) -> Organizador: ...

    @abstractmethod
    def obtener_por_id(self, id_organizador: UUID) -> Organizador | None: ...

    @abstractmethod
    def obtener_por_usuario(self, id_usuario: UUID) -> Organizador | None: ...