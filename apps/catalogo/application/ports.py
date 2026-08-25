"""
Puertos del contexto Catalogo (Dependency Inversion).

La capa de aplicacion depende de estas abstracciones; las implementaciones
concretas viven en `infrastructure/`. Cambiar de ORM, o convertir Identidad en
un microservicio remoto, solo obliga a escribir un adaptador nuevo.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from apps.catalogo.application.dtos import FiltroExperienciasDTO
from apps.catalogo.domain.models import CategoriaInteres, Experiencia, Ubicacion


class ExperienciaRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, experiencia: Experiencia) -> Experiencia: ...

    @abstractmethod
    def obtener_por_id(self, id_experiencia: UUID) -> Experiencia | None: ...

    @abstractmethod
    def buscar(self, filtro: FiltroExperienciasDTO) -> list[Experiencia]: ...

    @abstractmethod
    def listar_por_organizador(self, id_organizador: UUID) -> list[Experiencia]: ...

    @abstractmethod
    def asignar_categorias(
        self, experiencia: Experiencia, categorias: list[CategoriaInteres]
    ) -> None: ...

    @abstractmethod
    def descontar_cupo(self, id_experiencia: UUID, cantidad: int) -> bool:
        """Descuenta de forma atomica. Devuelve False si no alcanza el cupo."""

    @abstractmethod
    def reponer_cupo(self, id_experiencia: UUID, cantidad: int) -> None: ...


class UbicacionRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, ubicacion: Ubicacion) -> Ubicacion: ...

    @abstractmethod
    def obtener_por_id(self, id_ubicacion: UUID) -> Ubicacion | None: ...

    @abstractmethod
    def listar(self) -> list[Ubicacion]: ...


class CategoriaRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, categoria: CategoriaInteres) -> CategoriaInteres: ...

    @abstractmethod
    def listar_activas(self) -> list[CategoriaInteres]: ...

    @abstractmethod
    def obtener_muchas(self, ids: list[UUID]) -> list[CategoriaInteres]: ...


class OrganizadorPort(ABC):
    """Lo que Catalogo necesita saber de Identidad. Nada mas."""

    @abstractmethod
    def existe(self, id_organizador: UUID) -> bool: ...

    @abstractmethod
    def esta_verificado(self, id_organizador: UUID) -> bool: ...

    @abstractmethod
    def nombre_comercial(self, id_organizador: UUID) -> str: ...


class InteresesUsuarioPort(ABC):
    """Intereses declarados por un usuario: {id_categoria: nivel 1..5}."""

    @abstractmethod
    def obtener(self, id_usuario: UUID) -> dict[str, int]: ...
