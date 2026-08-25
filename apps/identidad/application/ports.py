"""Puertos del contexto Identidad (Dependency Inversion)."""
from abc import ABC, abstractmethod
from uuid import UUID

from apps.identidad.domain.models import InteresUsuario, Organizador, Usuario


class UsuarioRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def obtener_por_id(self, id_usuario: UUID) -> Usuario | None: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Usuario | None: ...

    @abstractmethod
    def existe_correo(self, correo: str) -> bool: ...

    @abstractmethod
    def listar(self) -> list[Usuario]: ...


class OrganizadorRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, organizador: Organizador) -> Organizador: ...

    @abstractmethod
    def obtener_por_id(self, id_organizador: UUID) -> Organizador | None: ...

    @abstractmethod
    def obtener_por_usuario(self, id_usuario: UUID) -> Organizador | None: ...


class InteresRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, interes: InteresUsuario) -> InteresUsuario: ...

    @abstractmethod
    def listar_por_usuario(self, id_usuario: UUID) -> list[InteresUsuario]: ...

    @abstractmethod
    def obtener(self, id_usuario: UUID, id_categoria: UUID) -> InteresUsuario | None: ...

    @abstractmethod
    def eliminar(self, id_usuario: UUID, id_categoria: UUID) -> bool: ...


class CatalogoCategoriasPort(ABC):
    """Lo unico que Identidad necesita de Catalogo: validar que existe."""

    @abstractmethod
    def existe_categoria(self, id_categoria: UUID) -> bool: ...
