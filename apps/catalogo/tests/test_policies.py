"""Pruebas de las politicas de dominio del Catalogo (sin Django ni BD)."""
from decimal import Decimal

import pytest

from apps.catalogo.domain.enums import EstadoExperiencia
from apps.catalogo.domain.exceptions import (
    DatosExperienciaInvalidos,
    TransicionExperienciaInvalida,
)
from apps.catalogo.domain.policies import (
    CalculadoraPrecio,
    CicloVidaExperiencia,
    PoliticaAfinidad,
    PoliticaAforo,
)


class TestCalculadoraPrecio:
    def test_redondea_a_dos_decimales(self):
        assert CalculadoraPrecio.normalizar(Decimal("1000.005")) == Decimal("1000.01")

    def test_rechaza_precio_negativo(self):
        with pytest.raises(DatosExperienciaInvalidos):
            CalculadoraPrecio.normalizar(Decimal("-1"))

    def test_aplica_descuento(self):
        assert CalculadoraPrecio.calcular_precio_final(
            Decimal("50000"), Decimal("0.20")
        ) == Decimal("40000.00")

    def test_rechaza_descuento_fuera_de_rango(self):
        with pytest.raises(DatosExperienciaInvalidos):
            CalculadoraPrecio.calcular_precio_final(Decimal("100"), Decimal("1.5"))

    def test_recaudo_total(self):
        assert CalculadoraPrecio.calcular_recaudo_total(
            Decimal("45000"), 7
        ) == Decimal("315000.00")


class TestPoliticaAforo:
    def test_no_admite_cupo_cero(self):
        with pytest.raises(DatosExperienciaInvalidos):
            PoliticaAforo.validar(0, 50)

    def test_sin_ubicacion_conocida_no_impone_techo(self):
        PoliticaAforo.validar(300, None)  # no lanza

    def test_disponibilidad(self):
        assert PoliticaAforo.hay_disponibilidad(5, 5)
        assert not PoliticaAforo.hay_disponibilidad(4, 5)
        assert not PoliticaAforo.hay_disponibilidad(10, 0)


class TestCicloVidaExperiencia:
    def test_una_cancelada_no_revive(self):
        with pytest.raises(TransicionExperienciaInvalida):
            CicloVidaExperiencia.validar_transicion(
                EstadoExperiencia.CANCELADA, EstadoExperiencia.PUBLICADA
            )

    def test_agotada_vuelve_a_publicada_al_liberarse_cupo(self):
        CicloVidaExperiencia.validar_transicion(
            EstadoExperiencia.AGOTADA, EstadoExperiencia.PUBLICADA
        )

    def test_solo_una_publicada_admite_reservas(self):
        assert CicloVidaExperiencia.es_reservable(EstadoExperiencia.PUBLICADA)
        assert not CicloVidaExperiencia.es_reservable(EstadoExperiencia.AGOTADA)
        assert not CicloVidaExperiencia.es_reservable(EstadoExperiencia.BORRADOR)


class TestPoliticaAfinidad:
    def test_sin_intereses_no_hay_afinidad(self):
        assert PoliticaAfinidad.calcular_coincidencia({}, {"a"}) == 0.0

    def test_sin_categorias_en_comun_no_hay_afinidad(self):
        assert PoliticaAfinidad.calcular_coincidencia({"a": 5}, {"b"}) == 0.0

    def test_coincidencia_perfecta_da_uno(self):
        assert PoliticaAfinidad.calcular_coincidencia({"a": 5}, {"a"}) == 1.0

    def test_mas_interes_declarado_da_mas_puntaje(self):
        alto = PoliticaAfinidad.calcular_coincidencia({"a": 5}, {"a"})
        bajo = PoliticaAfinidad.calcular_coincidencia({"a": 1}, {"a"})
        assert alto > bajo

    def test_cubrir_menos_categorias_baja_el_puntaje(self):
        total = PoliticaAfinidad.calcular_coincidencia({"a": 5, "b": 5}, {"a", "b"})
        parcial = PoliticaAfinidad.calcular_coincidencia({"a": 5}, {"a", "b"})
        assert total > parcial
