from abc import ABC, abstractmethod
from apps.integraciones.domain.dtos import ClimaDTO, PlanAliadoDTO


class ClimaPort(ABC):
    """
    Puerto para la API de Terceros de pronóstico del clima.
    Cumple el principio de Inversión de Dependencias (DIP) y el Patrón Adapter.
    """

    @abstractmethod
    def consultar_clima(
        self,
        ciudad: str,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> ClimaDTO:
        """Consulta el estado del tiempo para la ubicación de una experiencia."""


class ServicioAliadoPort(ABC):
    """
    Puerto para consumir la API del equipo aliado.
    Permite intercambiar el endpoint real HTTP por un mock o fallback resiliente.
    """

    @abstractmethod
    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        """Obtiene la lista de planes compartidos por el equipo aliado."""
