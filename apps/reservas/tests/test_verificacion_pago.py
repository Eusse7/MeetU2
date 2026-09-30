"""
Costura del Strangler Pattern: Reservas confirma solo con un pago que el
microservicio Flask de Pagos respalda.

El servicio se prueba con un verificador falso; el adaptador HTTP se prueba
simulando las respuestas del microservicio (sin red).
"""
import io
import json
import urllib.error
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from apps.reservas.application.dtos import ConfirmarReservaDTO, SolicitarReservaDTO
from apps.reservas.application.ports import VerificadorPagoPort
from apps.reservas.application.services import ConfirmarReservaService
from apps.reservas.domain.enums import EstadoReserva
from apps.reservas.domain.exceptions import PagoNoVerificado
from apps.reservas.infrastructure.adapters import (
    HttpVerificadorPago,
    ServicioPagosNoDisponible,
)
from apps.reservas.tests.test_services import (
    AHORA,
    ID_USUARIO,
    armar_solicitud,
    experiencia_vista,
    usuario_vista,
)
from apps.shared.tests.dobles import PerfilFalso


class VerificadorFalso(VerificadorPagoPort):
    def __init__(self, validas: set[str]):
        self.validas = validas
        self.llamadas = []

    def verificar(self, referencia, id_reserva, monto):
        self.llamadas.append((referencia, id_reserva, monto))
        if referencia not in self.validas:
            raise PagoNoVerificado(f"No existe un pago con referencia {referencia}")


def confirmar_con(verificador, referencia):
    experiencia = experiencia_vista()
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )
    servicio = ConfirmarReservaService(
        reservas=repo,
        catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()),
        notificador=notificador,
        reloj=lambda: AHORA + timedelta(minutes=1),
        verificador_pago=verificador,
    )
    return reserva, servicio.ejecutar(
        ConfirmarReservaDTO(id_reserva=reserva.id, referencia_pago=referencia)
    )


# ---------------------------------------------------------------- servicio
def test_confirma_con_referencia_respaldada_por_el_microservicio():
    verificador = VerificadorFalso({"PAG-OK"})
    reserva, confirmada = confirmar_con(verificador, "PAG-OK")

    assert confirmada.estado == EstadoReserva.CONFIRMADA
    assert verificador.llamadas == [("PAG-OK", reserva.id, reserva.monto_total)]


def test_referencia_inventada_es_409():
    with pytest.raises(PagoNoVerificado) as exc:
        confirmar_con(VerificadorFalso({"PAG-OK"}), "TX-INVENTADA")
    assert exc.value.status_code == 409


def test_sin_referencia_no_se_confirma_si_pagos_esta_activo():
    with pytest.raises(PagoNoVerificado):
        confirmar_con(VerificadorFalso(set()), "")


def test_sin_verificador_se_conserva_el_comportamiento_legado():
    _, confirmada = confirmar_con(None, "")
    assert confirmada.estado == EstadoReserva.CONFIRMADA


# -------------------------------------------------------- adaptador HTTP
class RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def simular_pago(monkeypatch, cuerpo=None, error=None):
    def urlopen(url, timeout):
        if error:
            raise error
        return RespuestaFalsa(json.dumps(cuerpo).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)


def test_adaptador_acepta_pago_aprobado_de_la_misma_reserva(monkeypatch):
    id_reserva = uuid4()
    simular_pago(
        monkeypatch,
        {"estado": "APROBADO", "id_reserva": str(id_reserva), "monto": "90000.00"},
    )
    HttpVerificadorPago("http://pagos:5000").verificar(
        "PAG-1", id_reserva, Decimal("90000.00")
    )


@pytest.mark.parametrize(
    "cambios",
    [
        {"estado": "RECHAZADO"},
        {"id_reserva": str(uuid4())},
        {"monto": "1.00"},
    ],
)
def test_adaptador_rechaza_pagos_que_no_respaldan_la_reserva(monkeypatch, cambios):
    id_reserva = uuid4()
    cuerpo = {"estado": "APROBADO", "id_reserva": str(id_reserva), "monto": "90000.00"}
    simular_pago(monkeypatch, {**cuerpo, **cambios})
    with pytest.raises(PagoNoVerificado):
        HttpVerificadorPago("http://pagos:5000").verificar(
            "PAG-1", id_reserva, Decimal("90000.00")
        )


def test_adaptador_traduce_404_a_pago_no_verificado(monkeypatch):
    simular_pago(
        monkeypatch,
        error=urllib.error.HTTPError("u", 404, "Not Found", {}, None),
    )
    with pytest.raises(PagoNoVerificado):
        HttpVerificadorPago("http://pagos:5000").verificar("X", uuid4(), Decimal("1"))


def test_adaptador_con_servicio_caido_es_503(monkeypatch):
    simular_pago(monkeypatch, error=urllib.error.URLError("connection refused"))
    with pytest.raises(ServicioPagosNoDisponible) as exc:
        HttpVerificadorPago("http://pagos:5000").verificar("X", uuid4(), Decimal("1"))
    assert exc.value.status_code == 503
