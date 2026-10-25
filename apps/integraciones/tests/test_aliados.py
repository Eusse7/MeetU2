"""Pruebas del Adaptador del Servicio a Consumir (API del equipo aliado)."""
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.integraciones.application.services import ConsultarPlanesAliadosUseCase
from apps.integraciones.infrastructure.aliado_adapters import (
    FallbackServicioAliadoAdapter,
    HttpServicioAliadoAdapter,
)


def test_fallback_aliados_retorna_planes_validos():
    adapter = FallbackServicioAliadoAdapter()
    planes = adapter.obtener_planes_aliados()

    assert len(planes) >= 3
    for p in planes:
        assert p.titulo
        assert p.precio > Decimal("0")
        assert p.cupos_disponibles > 0
        assert p.url_externa.startswith("http")


def test_http_aliados_con_payload_remoto():
    mock_payload = json.dumps([
        {
            "id": "ext-101",
            "titulo": "Cata de Cacao en Finca",
            "categoria": "Gastronomía",
            "ciudad": "Jericó",
            "precio": "45000",
            "organizador": "Equipo Aliado Sur",
            "cupos_disponibles": 8,
            "url": "https://aliado.org/cacao",
        }
    ]).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    adapter = HttpServicioAliadoAdapter(url="https://api.aliado.org/planes")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        planes = adapter.obtener_planes_aliados()

    assert len(planes) == 1
    assert planes[0].id == "ext-101"
    assert planes[0].titulo == "Cata de Cacao en Finca"
    assert planes[0].precio == Decimal("45000")


def test_http_aliados_con_falla_activa_fallback():
    adapter = HttpServicioAliadoAdapter(url="https://api.aliado-caido.org/planes")

    with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        planes = adapter.obtener_planes_aliados()

    assert len(planes) >= 3
    assert planes[0].id.startswith("aliado-")


def test_use_case_planes_aliados():
    adapter = FallbackServicioAliadoAdapter()
    use_case = ConsultarPlanesAliadosUseCase(aliado_adapter=adapter)
    planes = use_case.ejecutar()

    assert len(planes) >= 3
