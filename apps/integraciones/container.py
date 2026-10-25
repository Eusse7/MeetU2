"""
Contenedor de Inyección de Dependencias para el contexto de Integraciones.
Permite resolver adaptadores reales o simulados según la configuración.
"""
from django.conf import settings

from apps.integraciones.application.services import (
    ConsultarClimaUseCase,
    ConsultarEstadoReporteUseCase,
    ConsultarPlanesAliadosUseCase,
    ExponerExperienciasPublicasUseCase,
    SolicitarReporteAsincronoUseCase,
)
from apps.integraciones.domain.ports import ClimaPort, ServicioAliadoPort
from apps.integraciones.infrastructure.aliado_adapters import (
    FallbackServicioAliadoAdapter,
    HttpServicioAliadoAdapter,
)
from apps.integraciones.infrastructure.clima_adapters import (
    OpenMeteoClimaAdapter,
    SimuladoClimaAdapter,
)


def clima_adapter() -> ClimaPort:
    provider = getattr(settings, "CLIMA_PROVIDER", "open_meteo")
    if provider == "simulado":
        return SimuladoClimaAdapter()
    return OpenMeteoClimaAdapter()


def aliado_adapter() -> ServicioAliadoPort:
    url = getattr(settings, "SERVICIO_ALIADO_URL", "").strip()
    if url:
        return HttpServicioAliadoAdapter(url=url)
    return FallbackServicioAliadoAdapter()


def consultar_clima() -> ConsultarClimaUseCase:
    return ConsultarClimaUseCase(clima_adapter=clima_adapter())


def consultar_planes_aliados() -> ConsultarPlanesAliadosUseCase:
    return ConsultarPlanesAliadosUseCase(aliado_adapter=aliado_adapter())


def exponer_experiencias_publicas() -> ExponerExperienciasPublicasUseCase:
    return ExponerExperienciasPublicasUseCase()


def solicitar_reporte_asincrono() -> SolicitarReporteAsincronoUseCase:
    return SolicitarReporteAsincronoUseCase()


def consultar_estado_reporte() -> ConsultarEstadoReporteUseCase:
    return ConsultarEstadoReporteUseCase()
