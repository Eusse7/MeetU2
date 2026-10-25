"""Pruebas unitarias de las politicas de dominio del contexto Social."""
from decimal import Decimal
from uuid import uuid4

import pytest

from apps.social.domain.exceptions import (
    CalificacionInvalida,
    ReservaNoPerteneceAUsuario,
    ReservaSinCheckIn,
)
from apps.social.domain.policies import CalculadoraPromedio, PoliticaResena


def test_validar_asistencia_valida_correctamente():
    usuario_id = uuid4()
    # No lanza excepcion cuando todo coincide y tiene check-in
    PoliticaResena.validar_asistencia(
        id_usuario=usuario_id,
        reserva_usuario_id=usuario_id,
        reserva_estado="CHECK_IN",
        tiene_check_in=True,
    )


def test_validar_asistencia_rechaza_usuario_distinto():
    with pytest.raises(ReservaNoPerteneceAUsuario):
        PoliticaResena.validar_asistencia(
            id_usuario=uuid4(),
            reserva_usuario_id=uuid4(),
            reserva_estado="CHECK_IN",
            tiene_check_in=True,
        )


@pytest.mark.parametrize("estado", ["PENDIENTE_PAGO", "CONFIRMADA", "CANCELADA", "EXPIRADA"])
def test_validar_asistencia_rechaza_reserva_sin_check_in(estado):
    usuario_id = uuid4()
    with pytest.raises(ReservaSinCheckIn):
        PoliticaResena.validar_asistencia(
            id_usuario=usuario_id,
            reserva_usuario_id=usuario_id,
            reserva_estado=estado,
            tiene_check_in=False,
        )


def test_validar_asistencia_rechaza_check_in_nulo():
    usuario_id = uuid4()
    with pytest.raises(ReservaSinCheckIn):
        PoliticaResena.validar_asistencia(
            id_usuario=usuario_id,
            reserva_usuario_id=usuario_id,
            reserva_estado="CHECK_IN",
            tiene_check_in=False,
        )


@pytest.mark.parametrize("calificacion", [1, 2, 3, 4, 5])
def test_calificacion_valida(calificacion):
    PoliticaResena.validar_calificacion(calificacion)


@pytest.mark.parametrize("calificacion", [0, -1, 6, 10, "5", None])
def test_calificacion_invalida(calificacion):
    with pytest.raises(CalificacionInvalida):
        PoliticaResena.validar_calificacion(calificacion)


def test_calculadora_promedio_vacio():
    assert CalculadoraPromedio.calcular([]) == Decimal("0.00")


def test_calculadora_promedio_unico():
    assert CalculadoraPromedio.calcular([5]) == Decimal("5.00")


def test_calculadora_promedio_multiples():
    # (5 + 4 + 4) / 3 = 4.3333... -> 4.33
    assert CalculadoraPromedio.calcular([5, 4, 4]) == Decimal("4.33")
    # (5 + 4) / 2 = 4.5 -> 4.50
    assert CalculadoraPromedio.calcular([5, 4]) == Decimal("4.50")
