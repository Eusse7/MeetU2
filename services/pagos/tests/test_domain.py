"""Reglas puras del dominio de Pagos: sin Flask, sin base de datos."""
from decimal import Decimal
from uuid import uuid4

import pytest

from pagos_service.domain import (
    CalculadoraLiquidacion,
    EstadoPago,
    GeneradorReferencia,
    MedioPago,
    Pago,
    PoliticaPago,
)
from pagos_service.errors import ConflictoPago, DatosInvalidos
from pagos_service.gateways import (
    TOKEN_RECHAZADO,
    FakeGateway,
    PasarelaFactory,
    WompiSandboxGateway,
)


def pago(monto="100000.00", comision="10000.00", estado=EstadoPago.APROBADO):
    return Pago(
        id_reserva=uuid4(), id_usuario=uuid4(), id_organizador=uuid4(),
        monto=Decimal(monto), comision_plataforma=Decimal(comision),
        medio_pago=MedioPago.TARJETA, pasarela="fake", estado=estado,
        referencia="PAG-TEST",
    )


def test_neto_descuenta_la_comision():
    assert CalculadoraLiquidacion.neto_organizador(
        Decimal("100000"), Decimal("10000")
    ) == Decimal("90000.00")


def test_neto_con_reembolso_parcial_descuenta_lo_devuelto():
    assert CalculadoraLiquidacion.neto_organizador(
        Decimal("100000"), Decimal("10000"), Decimal("50000")
    ) == Decimal("40000.00")


def test_neto_con_reembolso_total_es_cero():
    assert CalculadoraLiquidacion.neto_organizador(
        Decimal("100000"), Decimal("10000"), Decimal("100000")
    ) == Decimal("0.00")


@pytest.mark.parametrize("medio", ["tarjeta", "PSE", " nequi "])
def test_medios_validos_se_normalizan(medio):
    assert PoliticaPago.validar_medio(medio) in set(MedioPago)


def test_medio_invalido_es_400():
    with pytest.raises(DatosInvalidos) as exc:
        PoliticaPago.validar_medio("bitcoin")
    assert exc.value.status_code == 400


def test_monto_cero_no_se_cobra():
    with pytest.raises(DatosInvalidos):
        PoliticaPago.validar_monto(Decimal("0"))


def test_reembolso_no_puede_superar_lo_cobrado():
    with pytest.raises(DatosInvalidos):
        PoliticaPago.validar_reembolso(pago(), Decimal("200000"))


def test_no_se_reembolsa_un_pago_rechazado():
    with pytest.raises(ConflictoPago):
        PoliticaPago.validar_reembolso(pago(estado=EstadoPago.RECHAZADO), Decimal("1"))


def test_estado_tras_reembolso():
    p = pago()
    assert PoliticaPago.estado_tras_reembolso(p, Decimal("50000")) == EstadoPago.REEMBOLSO_PARCIAL
    assert PoliticaPago.estado_tras_reembolso(p, Decimal("100000")) == EstadoPago.REEMBOLSADO


def test_referencias_son_unicas():
    referencias = {GeneradorReferencia.generar() for _ in range(200)}
    assert len(referencias) == 200
    assert all(r.startswith("PAG-") for r in referencias)


def test_factory_selecciona_la_pasarela():
    assert isinstance(PasarelaFactory.crear("fake"), FakeGateway)
    assert isinstance(PasarelaFactory.crear("WOMPI"), WompiSandboxGateway)
    with pytest.raises(DatosInvalidos):
        PasarelaFactory.crear("paypal")


def test_fake_gateway_rechaza_token_de_prueba():
    resultado = FakeGateway().cobrar("PAG-X", Decimal("1000"), "TARJETA", TOKEN_RECHAZADO)
    assert not resultado.aprobado
    assert resultado.motivo
