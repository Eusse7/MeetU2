"""
Patrón Adapter para el Servicio a Consumir (API del equipo aliado).
Permite integrar servicios de equipos compañeros o activar la contingencia simulada.
"""
import json
import logging
import urllib.request
from decimal import Decimal
from urllib.error import URLError

from django.conf import settings

from apps.integraciones.domain.dtos import PlanAliadoDTO
from apps.integraciones.domain.ports import ServicioAliadoPort

logger = logging.getLogger("meetu2.integraciones.aliados")


class FallbackServicioAliadoAdapter(ServicioAliadoPort):
    """
    Adaptador de contingencia que expone planes de la red aliada
    garantizando que la aplicación nunca falle ni muestre pantallas vacías.
    """

    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        return [
            PlanAliadoDTO(
                id="aliado-001",
                titulo="Ruta de Cafés de Especialidad y Tertulia",
                categoria="Gastronomía",
                ciudad="Medellín",
                precio=Decimal("38000"),
                organizador="Red Aliada CoffeeWalkers",
                cupos_disponibles=6,
                url_externa="https://aliado-eventos.edu.co/planes/cafes",
                red_aliada="Alianza Universitaria (Equipo Aliado)",
            ),
            PlanAliadoDTO(
                id="aliado-002",
                titulo="Taller de Coctelería de Autor y Botánica",
                categoria="Creatividad",
                ciudad="Medellín",
                precio=Decimal("55000"),
                organizador="Colectivo Mixology Lab",
                cupos_disponibles=4,
                url_externa="https://aliado-eventos.edu.co/planes/cocteles",
                red_aliada="Alianza Universitaria (Equipo Aliado)",
            ),
            PlanAliadoDTO(
                id="aliado-003",
                titulo="Torneo Relámpago de Juegos de Rol y Estrategia",
                categoria="Juegos de mesa",
                ciudad="Medellín",
                precio=Decimal("15000"),
                organizador="Gremio Rolero Universitario",
                cupos_disponibles=12,
                url_externa="https://aliado-eventos.edu.co/planes/rol",
                red_aliada="Alianza Universitaria (Equipo Aliado)",
            ),
        ]


class HttpServicioAliadoAdapter(ServicioAliadoPort):
    """
    Consume el servicio REST del equipo aliado mediante HTTP.
    Usa la URL configurada en SERVICIO_ALIADO_URL.
    """

    def __init__(self, url: str | None = None, timeout: float = 3.5):
        self._url = url or getattr(settings, "SERVICIO_ALIADO_URL", "").strip()
        self._timeout = timeout
        self._fallback = FallbackServicioAliadoAdapter()

    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        if not self._url:
            logger.info("SERVICIO_ALIADO_URL no configurada. Usando catálogo de red aliada.")
            return self._fallback.obtener_planes_aliados()

        try:
            req = urllib.request.Request(
                self._url,
                headers={"Accept": "application/json", "User-Agent": "MeetU2-Consumer/2.0"},
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            planes = []
            items = data if isinstance(data, list) else data.get("experiencias", data.get("planes", []))

            for it in items:
                planes.append(
                    PlanAliadoDTO(
                        id=str(it.get("id", f"aliado-{len(planes)+1}")),
                        titulo=str(it.get("titulo", it.get("nombre", "Plan de Aliado"))),
                        categoria=str(it.get("categoria", "General")),
                        ciudad=str(it.get("ciudad", "Medellín")),
                        precio=Decimal(str(it.get("precio", "0"))),
                        organizador=str(it.get("organizador", "Equipo Aliado")),
                        cupos_disponibles=int(it.get("cupos_disponibles", it.get("cupo_disponible", 5))),
                        url_externa=str(it.get("url", it.get("url_externa", self._url))),
                        red_aliada="Equipo Aliado (Integración HTTP en vivo)",
                    )
                )

            return planes if planes else self._fallback.obtener_planes_aliados()
        except (URLError, TimeoutError, json.JSONDecodeError, Exception) as exc:
            logger.warning(
                "Fallo al conectar con servicio aliado en %s (%s). Activando fallback de resiliencia.",
                self._url,
                exc,
            )
            return self._fallback.obtener_planes_aliados()
