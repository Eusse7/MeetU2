"""Pruebas del Adaptador de Clima (API de Terceros vía Inversión de Dependencias)."""
import json
from unittest.mock import MagicMock, patch

from apps.integraciones.application.services import ConsultarClimaUseCase
from apps.integraciones.infrastructure.clima_adapters import (
    OpenMeteoClimaAdapter,
    SimuladoClimaAdapter,
)


def test_simulado_clima_adapter_retorna_dto_valido():
    adapter = SimuladoClimaAdapter()
    clima = adapter.consultar_clima("Medellin")

    assert clima.ciudad == "Medellin"
    assert clima.temperatura_c > 0
    assert clima.icono == "☀️"
    assert "Simulado" in clima.proveedor


def test_open_meteo_adapter_exitoso():
    adapter = OpenMeteoClimaAdapter()
    mock_payload = json.dumps({
        "current": {
            "temperature_2m": 24.3,
            "weather_code": 0,
            "relative_humidity_2m": 58,
        }
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        clima = adapter.consultar_clima("Medellín", 6.2442, -75.5812)

    assert clima.temperatura_c == 24.3
    assert clima.icono == "☀️"
    assert "Despejado" in clima.descripcion
    assert "Open-Meteo" in clima.proveedor


def test_open_meteo_adapter_falla_activa_fallback_resiliente():
    adapter = OpenMeteoClimaAdapter()

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        clima = adapter.consultar_clima("Bogotá")

    assert clima.temperatura_c > 0
    assert "contingencia" in clima.proveedor.lower()


def test_use_case_consulta_clima():
    adapter = SimuladoClimaAdapter()
    use_case = ConsultarClimaUseCase(clima_adapter=adapter)
    clima = use_case.ejecutar("Cali")

    assert clima.ciudad == "Cali"
    assert clima.temperatura_c == 22.5
