"""Pruebas del Adaptador del Servicio a Consumir (API del equipo aliado de Hoteles)."""
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.integraciones.application.services import ConsultarPlanesAliadosUseCase
from apps.integraciones.infrastructure.aliado_adapters import (
    FallbackServicioAliadoAdapter,
    HttpServicioAliadoAdapter,
)


def test_fallback_aliados_retorna_hoteles_validos():
    adapter = FallbackServicioAliadoAdapter()
    hoteles = adapter.obtener_planes_aliados()

    assert len(hoteles) >= 3
    for h in hoteles:
        assert h.titulo
        assert h.precio > Decimal("0")
        assert h.cupos_disponibles > 0
        assert h.url_externa.startswith("http")
        assert h.estrellas >= 4.0
        assert len(h.amenidades) > 0


def test_http_aliados_con_payload_nativo_hotelero():
    mock_payload = json.dumps({
        "servicio": "Sistema Hotelero Aliado",
        "hoteles": [
            {
                "id_hotel": "ext-htl-101",
                "nombre_hotel": "Gran Hotel & Spa Plaza",
                "tipo_alojamiento": "Suite Ejecutiva",
                "ciudad": "Medellín",
                "precio_noche": "210000",
                "cadena": "Cadena Hotelera Estelar",
                "habitaciones_disponibles": 7,
                "estrellas": 4.9,
                "amenidades": ["Piscina", "Desayuno", "Spa"],
                "url_reserva": "https://hoteles-aliados.com/hotel/plaza",
                "imagen": "https://images.unsplash.com/photo-1566073771259-6a8506099945",
            }
        ]
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    adapter = HttpServicioAliadoAdapter(url="https://api.hoteles-aliados.com/v1/hoteles")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        hoteles = adapter.obtener_planes_aliados()

    assert len(hoteles) == 1
    assert hoteles[0].id == "ext-htl-101"
    assert hoteles[0].titulo == "Gran Hotel & Spa Plaza"
    assert hoteles[0].precio == Decimal("210000")
    assert hoteles[0].cupos_disponibles == 7
    assert hoteles[0].tipo_alojamiento == "Suite Ejecutiva"
    assert "Piscina" in hoteles[0].amenidades


def test_http_aliados_con_falla_activa_fallback():
    adapter = HttpServicioAliadoAdapter(url="https://api.aliado-caido.org/hoteles")

    with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        hoteles = adapter.obtener_planes_aliados()

    assert len(hoteles) >= 3
    assert hoteles[0].id.startswith("hotel-")


def test_use_case_planes_aliados():
    adapter = FallbackServicioAliadoAdapter()
    use_case = ConsultarPlanesAliadosUseCase(aliado_adapter=adapter)
    hoteles = use_case.ejecutar()

    assert len(hoteles) >= 3
    assert "Hotel" in hoteles[0].titulo or "Glamping" in hoteles[0].titulo or "Resort" in hoteles[0].titulo
