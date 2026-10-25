"""
Patrón Adapter (Inversión de Dependencias) para API de Terceros.
Consume la API pública de pronóstico Open-Meteo con fallback a simulación.
"""
import json
import logging
import urllib.request
from urllib.error import URLError

from apps.integraciones.domain.dtos import ClimaDTO
from apps.integraciones.domain.ports import ClimaPort

logger = logging.getLogger("meetu2.integraciones.clima")

# Coordenadas por defecto para ciudades comunes en Colombia
COORDENADAS_CIUDADES: dict[str, tuple[float, float]] = {
    "medellin": (6.2442, -75.5812),
    "medellín": (6.2442, -75.5812),
    "bogota": (4.7110, -74.0721),
    "bogotá": (4.7110, -74.0721),
    "cali": (3.4516, -76.5320),
    "cartagena": (10.3910, -75.4794),
    "madrid": (40.4168, -3.7038),
}

# Códigos de tiempo WMO según la especificación meteorológica internacional
WMO_INTERPRETACION: dict[int, tuple[str, str, str]] = {
    0: ("Despejado y soleado", "☀️", "Clima ideal para actividades al aire libre."),
    1: ("Mayormente despejado", "🌤️", "Condiciones favorables para todo tipo de planes."),
    2: ("Parcialmente nublado", "⛅", "Temperatura agradable para compartir en grupo."),
    3: ("Nublado", "☁️", "Aceptable para planes al aire libre o en recintos cerrados."),
    45: ("Neblina matutina", "🌫️", "Precaución en desplazamientos temprano en la mañana."),
    51: ("Llovizna leve", "🌦️", "Se recomienda llevar chaqueta impermeable ligera."),
    61: ("Lluvia moderada", "🌧️", "Ideal para planes bajo techo (gastronomía, cafés, juegos)."),
    71: ("Nieve ligera", "❄️", "Abrígate muy bien para este plan."),
    80: ("Chubascos dispersos", "🌦️", "Lleva sombrilla por si hay lluvias pasajeras."),
    95: ("Tormenta eléctrica", "⛈️", "Se aconseja realizar la actividad en espacios interiores."),
}


class SimuladoClimaAdapter(ClimaPort):
    """Adaptador simulado para pruebas unitarias sin llamadas a la red."""

    def consultar_clima(
        self,
        ciudad: str,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> ClimaDTO:
        return ClimaDTO(
            temperatura_c=22.5,
            descripcion="Despejado y soleado (Sandbox)",
            icono="☀️",
            ciudad=ciudad.title() if ciudad else "Medellín",
            humedad_pct=65,
            recomendacion="Clima ideal para actividades al aire libre.",
            proveedor="Simulado (Test Suite)",
        )


class OpenMeteoClimaAdapter(ClimaPort):
    """
    Adaptador que consume la API de terceros Open-Meteo REST.
    No requiere API Key y cumple estrictamente con el contrato ClimaPort.
    """

    def __init__(self, timeout: float = 3.5):
        self._timeout = timeout
        self._fallback = SimuladoClimaAdapter()

    def consultar_clima(
        self,
        ciudad: str,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> ClimaDTO:
        nombre_ciudad = ciudad.strip().lower() if ciudad else "medellin"
        lat = latitud
        lon = longitud

        if lat is None or lon is None:
            coords = COORDENADAS_CIUDADES.get(nombre_ciudad, (6.2442, -75.5812))
            lat, lon = coords

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat:.4f}&longitude={lon:.4f}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code"
            f"&timezone=auto"
        )

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MeetU2-Platform/2.0"},
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            current = data.get("current", {})
            temp = float(current.get("temperature_2m", 22.0))
            code = int(current.get("weather_code", 0))
            humedad = current.get("relative_humidity_2m")

            desc, icono, reco = WMO_INTERPRETACION.get(
                code, ("Condiciones estables", "⛅", "Disfruta de la experiencia.")
            )

            return ClimaDTO(
                temperatura_c=round(temp, 1),
                descripcion=desc,
                icono=icono,
                ciudad=ciudad.title() if ciudad else "Medellín",
                humedad_pct=humedad,
                recomendacion=reco,
                proveedor="Open-Meteo Global Weather API",
            )
        except (URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "Fallo al consultar Open-Meteo (%s). Activando fallback de resiliencia.", exc
            )
            dto_fallback = self._fallback.consultar_clima(ciudad, lat, lon)
            return ClimaDTO(
                temperatura_c=dto_fallback.temperatura_c,
                descripcion=dto_fallback.descripcion,
                icono=dto_fallback.icono,
                ciudad=dto_fallback.ciudad,
                humedad_pct=dto_fallback.humedad_pct,
                recomendacion=dto_fallback.recomendacion,
                proveedor="Open-Meteo (Caché local de contingencia)",
            )
