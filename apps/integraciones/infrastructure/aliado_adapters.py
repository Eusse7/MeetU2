"""
Patrón Adapter para el Servicio a Consumir (API del equipo aliado).
Permite integrar servicios de la red hotelera aliada o activar la contingencia de alta disponibilidad.
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
    Adaptador de contingencia que expone la oferta hotelera de la red aliada
    (Servicio de Hoteles) garantizando que la aplicación nunca falle ni muestre pantallas vacías.
    """

    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        return [
            PlanAliadoDTO(
                id="hotel-001",
                titulo="Hotel Boutique & Spa El Poblado",
                categoria="Hotel & Spa",
                ciudad="Medellín",
                precio=Decimal("220000"),
                organizador="Cadena Hotelera Estelar (Red Aliada)",
                cupos_disponibles=5,
                url_externa="https://hoteles-aliados.com/hotel/poblado-boutique",
                red_aliada="Red Hotelera Aliada (Servicio de Hoteles)",
                amenidades=("☕ Desayuno buffet", "🏊 Piscina en terraza", "🧖 Spa & Sauna", "📶 WiFi 500 Mbps"),
                estrellas=4.9,
                tipo_alojamiento="Suite Deluxe con Balcón",
                imagen_url="https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&auto=format&fit=crop",
            ),
            PlanAliadoDTO(
                id="hotel-002",
                titulo="Eco-Lodge & Glamping Santa Elena",
                categoria="Glamping & Naturaleza",
                ciudad="Santa Elena",
                precio=Decimal("185000"),
                organizador="EcoHoteles Antioquia (Red Aliada)",
                cupos_disponibles=3,
                url_externa="https://hoteles-aliados.com/hotel/glamping-santa-elena",
                red_aliada="Red Hotelera Aliada (Servicio de Hoteles)",
                amenidades=("🔥 Fogata nocturna", "🛁 Jacuzzi privado", "🍳 Desayuno campesino", "🌿 Vista panorámica"),
                estrellas=4.8,
                tipo_alojamiento="Domo Geodésico con Jacuzzi",
                imagen_url="https://images.unsplash.com/photo-1587061949409-02df41d5e562?w=800&auto=format&fit=crop",
            ),
            PlanAliadoDTO(
                id="hotel-003",
                titulo="Hotel Terraza Laureles Urban & Rooftop",
                categoria="Hotel Urbano",
                ciudad="Medellín",
                precio=Decimal("160000"),
                organizador="Urban Boutique Hotels (Red Aliada)",
                cupos_disponibles=6,
                url_externa="https://hoteles-aliados.com/hotel/laureles-urban",
                red_aliada="Red Hotelera Aliada (Servicio de Hoteles)",
                amenidades=("🍹 Rooftop Bar", "☕ Cafetería de autor", "🏋️ Gimnasio", "📶 WiFi 500 Mbps"),
                estrellas=4.7,
                tipo_alojamiento="Habitación Superior King",
                imagen_url="https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop",
            ),
            PlanAliadoDTO(
                id="hotel-004",
                titulo="Resort & Cabañas Guatapé Lakefront",
                categoria="Resort Lacustre",
                ciudad="Guatapé",
                precio=Decimal("290000"),
                organizador="Lakeside Resorts (Red Aliada)",
                cupos_disponibles=4,
                url_externa="https://hoteles-aliados.com/hotel/guatape-resort",
                red_aliada="Red Hotelera Aliada (Servicio de Hoteles)",
                amenidades=("⛵ Muelle náutico", "🏊 Piscina infinita", "🍽️ Restaurante lacustre", "🚴 Kayaks incluidos"),
                estrellas=4.9,
                tipo_alojamiento="Cabaña frente al Embalse",
                imagen_url="https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&auto=format&fit=crop",
            ),
        ]


class HttpServicioAliadoAdapter(ServicioAliadoPort):
    """
    Consume el servicio REST del equipo aliado (Servicio de Hoteles) mediante HTTP
    implementando el patrón Adapter para transformar su esquema al modelo de dominio.
    Usa la URL configurada en SERVICIO_ALIADO_URL.
    """

    def __init__(self, url: str | None = None, timeout: float = 3.5):
        self._url = url or getattr(settings, "SERVICIO_ALIADO_URL", "").strip()
        self._timeout = timeout
        self._fallback = FallbackServicioAliadoAdapter()

    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        if not self._url:
            logger.info("SERVICIO_ALIADO_URL no configurada. Usando catálogo de red hotelera aliada.")
            return self._fallback.obtener_planes_aliados()

        try:
            req = urllib.request.Request(
                self._url,
                headers={"Accept": "application/json", "User-Agent": "MeetU2-Consumer/2.0"},
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            planes = []
            items = (
                data
                if isinstance(data, list)
                else data.get(
                    "hoteles",
                    data.get("alojamientos", data.get("hospedajes", data.get("planes", data.get("experiencias", [])))),
                )
            )

            for it in items:
                amenidades_raw = it.get("amenidades", it.get("servicios_incluidos", []))
                amenidades_tuple = tuple(amenidades_raw) if isinstance(amenidades_raw, list) else ()
                planes.append(
                    PlanAliadoDTO(
                        id=str(it.get("id_hotel", it.get("id", f"hotel-{len(planes)+1}"))),
                        titulo=str(it.get("nombre_hotel", it.get("nombre", it.get("titulo", "Hotel Aliado")))),
                        categoria=str(it.get("tipo_alojamiento", it.get("tipo_hospedaje", it.get("categoria", "Hotel & Hospedaje")))),
                        tipo_alojamiento=str(it.get("habitacion", it.get("tipo_alojamiento", it.get("tipo", "Habitación Estándar")))),
                        ciudad=str(it.get("ciudad", "Medellín")),
                        precio=Decimal(str(it.get("precio_noche", it.get("tarifa_noche", it.get("precio", "0"))))),
                        organizador=str(it.get("cadena", it.get("hotel", it.get("organizador", it.get("proveedor", "Red Hotelera Aliada"))))),
                        cupos_disponibles=int(it.get("habitaciones_disponibles", it.get("habitaciones_libres", it.get("cupos_disponibles", it.get("cupo_disponible", 3))))),
                        url_externa=str(it.get("url_reserva", it.get("enlace_reserva", it.get("url_externa", it.get("url", self._url))))),
                        red_aliada=str(it.get("red_aliada", "Red Hotelera Aliada (Integración HTTP en vivo)")),
                        amenidades=amenidades_tuple,
                        estrellas=float(it.get("estrellas", it.get("calificacion", 4.8))),
                        imagen_url=str(it.get("imagen", it.get("foto_url", it.get("imagen_url", "")))),
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
