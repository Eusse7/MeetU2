"""
Pruebas de las politicas de dominio de Reservas.

Son las reglas que definen el modelo de negocio (comision, reembolso, ventana
de check-in). Se prueban sin Django ni base de datos.
"""
from datetime import datetime, timedelta, timezone as tz
from decimal import Decimal

import pytest

from apps.reservas.domain.enums import EstadoReserva
from apps.reservas.domain.exceptions import (
    CheckInFueraDeVentana,
    DatosReservaInvalidos,
    TransicionReservaInvalida,
)
from apps.reservas.domain.policies import (
    CalculadoraMontos,
    GeneradorTicket,
    MaquinaEstadosReserva,
    PoliticaCancelacion,
    PoliticaCheckIn,
    PoliticaCupos,
    PoliticaExpiracion,
)

EVENTO = datetime(2026, 9, 10, 20, 0, tzinfo=tz.utc)


class TestCalculadoraMontos:
    def test_total_es_precio_por_cantidad(self):
        assert CalculadoraMontos.calcular_total(Decimal("45000"), 3) == Decimal(
            "135000.00"
        )

    def test_rechaza_cantidad_no_positiva(self):
        with pytest.raises(DatosReservaInvalidos):
            CalculadoraMontos.calcular_total(Decimal("45000"), 0)

    def test_comision_del_diez_por_ciento(self):
        assert CalculadoraMontos.calcular_comision(
            Decimal("135000"), Decimal("0.10")
        ) == Decimal("13500.00")

    def test_el_neto_del_organizador_es_el_total_menos_la_comision(self):
        total = Decimal("135000.00")
        comision = CalculadoraMontos.calcular_comision(total, Decimal("0.10"))
        assert CalculadoraMontos.calcular_neto_organizador(total, comision) == Decimal(
            "121500.00"
        )

    def test_rechaza_comision_fuera_de_rango(self):
        with pytest.raises(DatosReservaInvalidos):
            CalculadoraMontos.calcular_comision(Decimal("100"), Decimal("1.2"))


class TestPoliticaCupos:
    def test_respeta_el_maximo_por_reserva(self):
        assert PoliticaCupos.validar_cantidad(5, 5) == 5
        with pytest.raises(DatosReservaInvalidos):
            PoliticaCupos.validar_cantidad(6, 5)


class TestPoliticaExpiracion:
    def test_calcula_el_vencimiento(self):
        creada = EVENTO
        assert PoliticaExpiracion.calcular_vencimiento(creada, 30) == creada + timedelta(
            minutes=30
        )

    def test_detecta_vencimiento(self):
        vence = EVENTO
        assert PoliticaExpiracion.esta_vencida(vence, EVENTO + timedelta(seconds=1))
        assert not PoliticaExpiracion.esta_vencida(vence, EVENTO - timedelta(minutes=1))

    def test_sin_vencimiento_nunca_expira(self):
        assert not PoliticaExpiracion.esta_vencida(None, EVENTO)


class TestPoliticaCancelacion:
    @pytest.mark.parametrize(
        "horas_antes,porcentaje",
        [(72, "1.00"), (48, "1.00"), (47, "0.50"), (24, "0.50"), (23, "0.00"), (0, "0.00")],
    )
    def test_escala_de_reembolso(self, horas_antes, porcentaje):
        momento = EVENTO - timedelta(hours=horas_antes)
        assert PoliticaCancelacion.porcentaje_reembolso(EVENTO, momento) == Decimal(
            porcentaje
        )

    def test_calcula_el_monto_a_devolver(self):
        momento = EVENTO - timedelta(hours=30)
        assert PoliticaCancelacion.calcular_reembolso(
            Decimal("90000"), EVENTO, momento
        ) == Decimal("45000.00")

    def test_cancelar_despues_del_evento_no_reembolsa(self):
        momento = EVENTO + timedelta(hours=2)
        assert PoliticaCancelacion.calcular_reembolso(
            Decimal("90000"), EVENTO, momento
        ) == Decimal("0.00")

    def test_si_cancela_el_organizador_se_devuelve_todo(self):
        assert PoliticaCancelacion.reembolso_total_por_cancelacion_del_organizador(
            Decimal("90000")
        ) == Decimal("90000.00")


class TestMaquinaEstadosReserva:
    def test_una_pendiente_puede_confirmarse(self):
        MaquinaEstadosReserva.validar_transicion(
            EstadoReserva.PENDIENTE_PAGO, EstadoReserva.CONFIRMADA
        )

    def test_una_cancelada_no_puede_confirmarse(self):
        with pytest.raises(TransicionReservaInvalida) as exc:
            MaquinaEstadosReserva.validar_transicion(
                EstadoReserva.CANCELADA, EstadoReserva.CONFIRMADA
            )
        assert exc.value.status_code == 409

    def test_no_se_hace_check_in_sin_confirmar(self):
        with pytest.raises(TransicionReservaInvalida):
            MaquinaEstadosReserva.validar_transicion(
                EstadoReserva.PENDIENTE_PAGO, EstadoReserva.CHECK_IN
            )

    @pytest.mark.parametrize(
        "estado,retiene",
        [
            (EstadoReserva.PENDIENTE_PAGO, True),
            (EstadoReserva.CONFIRMADA, True),
            (EstadoReserva.CHECK_IN, True),
            (EstadoReserva.CANCELADA, False),
            (EstadoReserva.EXPIRADA, False),
        ],
    )
    def test_que_estados_retienen_cupo(self, estado, retiene):
        assert MaquinaEstadosReserva.retiene_cupo(estado) is retiene


class TestPoliticaCheckIn:
    def test_dentro_de_la_ventana_pasa(self):
        PoliticaCheckIn.validar_ventana(EVENTO, EVENTO - timedelta(hours=1), 3)

    def test_demasiado_pronto_falla(self):
        with pytest.raises(CheckInFueraDeVentana):
            PoliticaCheckIn.validar_ventana(EVENTO, EVENTO - timedelta(days=2), 3)

    def test_demasiado_tarde_falla(self):
        with pytest.raises(CheckInFueraDeVentana):
            PoliticaCheckIn.validar_ventana(EVENTO, EVENTO + timedelta(hours=5), 3)


class TestGeneradorTicket:
    def test_longitud_y_alfabeto_sin_ambiguedades(self):
        codigo = GeneradorTicket.generar()
        assert len(codigo) == 8
        assert not set(codigo) & set("OI01")

    def test_dos_tickets_seguidos_no_coinciden(self):
        codigos = {GeneradorTicket.generar() for _ in range(100)}
        assert len(codigos) > 95
