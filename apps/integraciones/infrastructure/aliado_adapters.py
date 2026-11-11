"""
Patrón Adapter para el Servicio a Consumir (API hotelMDJ).
Permite integrar la oferta de habitaciones de nuestro hotel aliado hotelMDJ
adaptando su esquema de habitaciones (rooms/room_type) al modelo canónico de MeetU2.
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

IMAGENES_TIPO_HABITACION = {
    "sencilla": "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop",
    "doble": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&auto=format&fit=crop",
    "familiar": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop",
    "suite": "https://images.unsplash.com/photo-1587061949409-02df41d5e562?w=800&auto=format&fit=crop",
}


def _construir_amenidades_habitacion(
    rt_name: str, bed_type: str, max_cap: int, floor: int, desc: str
) -> tuple[str, ...]:
    amenidades = [f"🛌 {bed_type}", f"👥 Hasta {max_cap} pers.", f"🏢 Piso {floor}"]
    desc_lower = desc.lower()
    if "patio" in desc_lower:
        amenidades.append("🌿 Patio interior")
    elif "balcon" in desc_lower or "balcón" in desc_lower:
        amenidades.append("🌅 Balcón vista al valle")
    elif "tina" in desc_lower:
        amenidades.append("🛁 Baño con tina")
    elif "ducha" in desc_lower:
        amenidades.append("🚿 Ducha de lluvia")
    amenidades.append("📶 WiFi 500 Mbps")
    return tuple(amenidades[:4])


def _mapear_room_a_dto(room: dict) -> PlanAliadoDTO:
    rt = room.get("room_type") or {}
    num = str(room.get("number", room.get("id", "101")))
    floor = room.get("floor", 1)
    rt_name = str(rt.get("name", "Habitación"))
    bed_type = str(rt.get("bed_type", "Cama estándar"))
    max_cap = int(rt.get("max_capacity", 2))
    price_val = Decimal(str(rt.get("base_price_per_night", "180000.00")))
    desc = str(rt.get("description", ""))

    img_list = room.get("image_urls") or []
    img_url = (
        img_list[0]
        if img_list
        else IMAGENES_TIPO_HABITACION.get(rt_name.lower(), IMAGENES_TIPO_HABITACION["sencilla"])
    )

    rt_lower = rt_name.lower()
    if "suite" in rt_lower:
        estrellas = 4.9
    elif "familiar" in rt_lower:
        estrellas = 4.8
    elif "doble" in rt_lower:
        estrellas = 4.8
    else:
        estrellas = 4.7

    return PlanAliadoDTO(
        id=f"hotel-mdj-hab-{num}",
        titulo=f"Nuestro Hotel Aliado hotelMDJ — Habitación {num} ({rt_name})",
        categoria=f"Habitación {rt_name}",
        tipo_alojamiento=f"{rt_name} · {bed_type} (Piso {floor})",
        ciudad="Medellín",
        precio=price_val,
        organizador="hotelMDJ (Nuestro Hotel Aliado)",
        cupos_disponibles=max_cap,
        url_externa=f"https://hotelmdj.com/rooms/{num}",
        red_aliada="hotelMDJ (Nuestro Hotel Aliado)",
        amenidades=_construir_amenidades_habitacion(rt_name, bed_type, max_cap, floor, desc),
        estrellas=estrellas,
        imagen_url=img_url,
    )


ROOMS_DATASET_DEFAULT = [
    {
        "id": 1,
        "number": "101",
        "floor": 1,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 1,
            "name": "Sencilla",
            "description": "Para una persona. Cama sencilla, escritorio junto a la ventana y bano con ducha. Da al patio interior, el lado silencioso de la casa.",
            "max_capacity": 1,
            "bed_type": "Cama sencilla",
            "base_price_per_night": "180000.00",
        },
    },
    {
        "id": 2,
        "number": "102",
        "floor": 1,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 1,
            "name": "Sencilla",
            "description": "Para una persona. Cama sencilla, escritorio junto a la ventana y bano con ducha. Da al patio interior, el lado silencioso de la casa.",
            "max_capacity": 1,
            "bed_type": "Cama sencilla",
            "base_price_per_night": "180000.00",
        },
    },
    {
        "id": 3,
        "number": "103",
        "floor": 1,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 2,
            "name": "Doble",
            "description": "Cama doble, zona de estar y bano con ducha de lluvia. Algunas dan al patio y otras a la carrera 43A.",
            "max_capacity": 2,
            "bed_type": "Cama doble",
            "base_price_per_night": "260000.00",
        },
    },
    {
        "id": 4,
        "number": "201",
        "floor": 2,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 2,
            "name": "Doble",
            "description": "Cama doble, zona de estar y bano con ducha de lluvia. Algunas dan al patio y otras a la carrera 43A.",
            "max_capacity": 2,
            "bed_type": "Cama doble",
            "base_price_per_night": "260000.00",
        },
    },
    {
        "id": 5,
        "number": "202",
        "floor": 2,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 2,
            "name": "Doble",
            "description": "Cama doble, zona de estar y bano con ducha de lluvia. Algunas dan al patio y otras a la carrera 43A.",
            "max_capacity": 2,
            "bed_type": "Cama doble",
            "base_price_per_night": "260000.00",
        },
    },
    {
        "id": 6,
        "number": "203",
        "floor": 2,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 3,
            "name": "Familiar",
            "description": "Dos camas dobles y bano amplio con tina. Pensada para familias o grupos de hasta cuatro personas.",
            "max_capacity": 4,
            "bed_type": "Dos camas dobles",
            "base_price_per_night": "390000.00",
        },
    },
    {
        "id": 7,
        "number": "301",
        "floor": 3,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 3,
            "name": "Familiar",
            "description": "Dos camas dobles y bano amplio con tina. Pensada para familias o grupos de hasta cuatro personas.",
            "max_capacity": 4,
            "bed_type": "Dos camas dobles",
            "base_price_per_night": "390000.00",
        },
    },
    {
        "id": 8,
        "number": "302",
        "floor": 3,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 4,
            "name": "Suite",
            "description": "Cama king, sala independiente, tina y balcon privado con vista al valle de Aburra. La habitacion mas grande del hotel.",
            "max_capacity": 4,
            "bed_type": "Cama king",
            "base_price_per_night": "520000.00",
        },
    },
    {
        "id": 9,
        "number": "401",
        "floor": 4,
        "status": "AVAILABLE",
        "image_urls": [],
        "room_type": {
            "id": 4,
            "name": "Suite",
            "description": "Cama king, sala independiente, tina y balcon privado con vista al valle de Aburra. La habitacion mas grande del hotel.",
            "max_capacity": 4,
            "bed_type": "Cama king",
            "base_price_per_night": "520000.00",
        },
    },
    {
        "id": 10,
        "number": "402",
        "floor": 4,
        "status": "MAINTENANCE",
        "image_urls": [],
        "room_type": {
            "id": 4,
            "name": "Suite",
            "description": "Cama king, sala independiente, tina y balcon privado con vista al valle de Aburra. La habitacion mas grande del hotel.",
            "max_capacity": 4,
            "bed_type": "Cama king",
            "base_price_per_night": "520000.00",
        },
    },
]


class FallbackServicioAliadoAdapter(ServicioAliadoPort):
    """
    Adaptador de contingencia que expone la oferta de habitaciones de nuestro hotel aliado hotelMDJ,
    garantizando que la aplicación nunca falle ni muestre pantallas vacías.
    """

    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        return [
            _mapear_room_a_dto(r)
            for r in ROOMS_DATASET_DEFAULT
            if str(r.get("status", "AVAILABLE")).upper() == "AVAILABLE"
        ]


class HttpServicioAliadoAdapter(ServicioAliadoPort):
    """
    Consume el servicio REST del equipo aliado hotelMDJ mediante HTTP
    implementando el patrón Adapter para transformar su esquema de habitaciones
    al modelo de dominio canónico PlanAliadoDTO.
    Usa la URL configurada en SERVICIO_ALIADO_URL.
    """

    def __init__(self, url: str | None = None, timeout: float = 3.5):
        self._url = url or getattr(settings, "SERVICIO_ALIADO_URL", "").strip()
        self._timeout = timeout
        self._fallback = FallbackServicioAliadoAdapter()

    def obtener_planes_aliados(self) -> list[PlanAliadoDTO]:
        if not self._url:
            logger.info("SERVICIO_ALIADO_URL no configurada. Usando catálogo hotelMDJ.")
            return self._fallback.obtener_planes_aliados()

        try:
            req = urllib.request.Request(
                self._url,
                headers={"Accept": "application/json", "User-Agent": "MeetU2-Consumer/2.0"},
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            planes = []

            # 1. Caso primario: Formato de habitaciones del hotel aliado ("rooms")
            if isinstance(data, dict) and "rooms" in data:
                for r in data.get("rooms", []):
                    if str(r.get("status", "AVAILABLE")).upper() != "AVAILABLE":
                        continue
                    planes.append(_mapear_room_a_dto(r))
                return planes if planes else self._fallback.obtener_planes_aliados()

            # 2. Caso secundario: compatibilidad con esquema genérico previo
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
                        titulo=str(it.get("nombre_hotel", it.get("nombre", it.get("titulo", "Nuestro Hotel Aliado hotelMDJ")))),
                        categoria=str(it.get("tipo_alojamiento", it.get("tipo_hospedaje", it.get("categoria", "Habitación Hotel")))),
                        tipo_alojamiento=str(it.get("habitacion", it.get("tipo_alojamiento", it.get("tipo", "Habitación Estándar")))),
                        ciudad=str(it.get("ciudad", "Medellín")),
                        precio=Decimal(str(it.get("precio_noche", it.get("tarifa_noche", it.get("precio", "0"))))),
                        organizador=str(it.get("cadena", it.get("hotel", it.get("organizador", it.get("proveedor", "hotelMDJ (Nuestro Hotel Aliado)"))))),
                        cupos_disponibles=int(it.get("habitaciones_disponibles", it.get("habitaciones_libres", it.get("cupos_disponibles", it.get("cupo_disponible", 2))))),
                        url_externa=str(it.get("url_reserva", it.get("enlace_reserva", it.get("url_externa", it.get("url", self._url))))),
                        red_aliada=str(it.get("red_aliada", "hotelMDJ (Nuestro Hotel Aliado)")),
                        amenidades=amenidades_tuple,
                        estrellas=float(it.get("estrellas", it.get("calificacion", 4.8))),
                        imagen_url=str(it.get("imagen", it.get("foto_url", it.get("imagen_url", "")))),
                    )
                )

            return planes if planes else self._fallback.obtener_planes_aliados()
        except (URLError, TimeoutError, json.JSONDecodeError, Exception) as exc:
            logger.warning(
                "Fallo al conectar con servicio aliado hotelMDJ en %s (%s). Activando fallback de resiliencia.",
                self._url,
                exc,
            )
            return self._fallback.obtener_planes_aliados()
