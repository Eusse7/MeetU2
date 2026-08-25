"""
Pruebas del `ExperienciaBuilder`.

Verifican lo que justifica el patron: cada paso valida su propia regla y el
producto final nace con sus invariantes ya satisfechas.
"""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.catalogo.application.builders import ExperienciaBuilder
from apps.catalogo.domain.enums import EstadoExperiencia
from apps.catalogo.domain.exceptions import AforoExcedido, DatosExperienciaInvalidos
from apps.catalogo.domain.models import Ubicacion

AHORA = timezone.now()


def ubicacion(aforo: int = 50) -> Ubicacion:
    return Ubicacion(
        id=uuid4(),
        nombre="Casa Rose",
        direccion="Cra 35",
        ciudad="Medellin",
        latitud=6.2,
        longitud=-75.5,
        aforo_maximo=aforo,
    )


def builder_completo(**cambios) -> ExperienciaBuilder:
    lugar = cambios.get("ubicacion", ubicacion())
    return (
        ExperienciaBuilder(ahora=AHORA)
        .para_organizador(cambios.get("organizador", uuid4()))
        .con_titulo(cambios.get("titulo", "Cata de cafes de origen"))
        .en_ubicacion(lugar)
        .en_fecha(cambios.get("fecha", AHORA + timedelta(days=3)))
        .con_precio(cambios.get("precio", Decimal("45000")))
        .con_cupo(cambios.get("cupo", 12))
    )


def test_la_experiencia_nace_con_todo_el_cupo_libre():
    experiencia = builder_completo().publicada().construir()

    assert experiencia.cupo_disponible == experiencia.cupo_maximo == 12
    assert experiencia.estado == EstadoExperiencia.PUBLICADA


def test_por_defecto_queda_en_borrador():
    assert builder_completo().construir().estado == EstadoExperiencia.BORRADOR


def test_el_cupo_no_puede_superar_el_aforo_de_la_ubicacion():
    with pytest.raises(AforoExcedido) as exc:
        builder_completo(ubicacion=ubicacion(aforo=10), cupo=11)

    assert exc.value.status_code == 400


def test_rechaza_fecha_en_el_pasado():
    with pytest.raises(DatosExperienciaInvalidos):
        builder_completo(fecha=AHORA - timedelta(hours=1))


def test_rechaza_fecha_sin_antelacion_minima():
    with pytest.raises(DatosExperienciaInvalidos):
        builder_completo(fecha=AHORA + timedelta(minutes=30))


def test_rechaza_titulo_demasiado_corto():
    with pytest.raises(DatosExperienciaInvalidos):
        builder_completo(titulo="Ok")


def test_aplica_el_descuento_al_precio():
    experiencia = (
        ExperienciaBuilder(ahora=AHORA)
        .para_organizador(uuid4())
        .con_titulo("Taller de ceramica")
        .en_ubicacion(ubicacion())
        .en_fecha(AHORA + timedelta(days=5))
        .con_precio(Decimal("100000"), descuento_porcentaje=Decimal("0.25"))
        .con_cupo(8)
        .construir()
    )

    assert experiencia.precio == Decimal("75000.00")


def test_construir_sin_datos_obligatorios_falla_indicando_cuales():
    builder = ExperienciaBuilder(ahora=AHORA).con_titulo("Cata de cafes")

    with pytest.raises(DatosExperienciaInvalidos) as exc:
        builder.construir()

    assert "organizador" in str(exc.value)
    assert "ubicacion" in str(exc.value)
