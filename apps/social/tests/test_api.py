"""Pruebas de integracion sobre HTTP para el contexto Social."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalogo import container as catalogo
from apps.catalogo.application.dtos import (
    CrearCategoriaDTO,
    CrearUbicacionDTO,
    PublicarExperienciaDTO,
)
from apps.identidad import container as identidad
from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
)
from apps.reservas import container as reservas
from apps.reservas.application.dtos import (
    CheckInDTO,
    ConfirmarReservaDTO,
    SolicitarReservaDTO,
)

SOCIAL = "/api/v1/social"


@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def escenario_completo(db):
    """Crea un host verificado, un asistente, experiencia y reserva con check-in."""
    host = identidad.registrar_usuario().ejecutar(
        RegistrarUsuarioDTO(nombre="Laura Host", correo="laura.social@meetu2.co")
    )
    org = identidad.convertir_en_organizador().ejecutar(
        ConvertirEnOrganizadorDTO(
            id_usuario=host.id,
            nombre_comercial="Experiencias Gourmet",
            cuenta_bancaria="987654321",
        )
    )
    identidad.verificar_organizador().ejecutar(org.id, True)

    cat = catalogo.crear_categoria().ejecutar(
        CrearCategoriaDTO(nombre="Cafe & Catas", descripcion="Catas")
    )
    ubi = catalogo.crear_ubicacion().ejecutar(
        CrearUbicacionDTO(
            nombre="Cafe Central",
            direccion="Calle 10",
            ciudad="Medellin",
            latitud=6.2,
            longitud=-75.5,
            aforo_maximo=30,
        )
    )

    ahora = timezone.now()
    exp = catalogo.publicar_experiencia().ejecutar(
        PublicarExperienciaDTO(
            id_organizador=org.id,
            id_ubicacion=ubi.id,
            titulo="Cata de Espresso",
            descripcion="Aprende a catar espresso.",
            fecha_hora=ahora + timedelta(hours=2, minutes=30),
            precio=Decimal("35000"),
            cupo_maximo=10,
            categorias=(cat.id,),
        )
    )

    asistente = identidad.registrar_usuario().ejecutar(
        RegistrarUsuarioDTO(nombre="Carlos Asistente", correo="carlos.social@meetu2.co")
    )

    reserva = reservas.solicitar_reserva().ejecutar(
        SolicitarReservaDTO(
            id_usuario=asistente.id,
            id_experiencia=exp.id,
            cantidad_cupos=1,
        )
    )
    reservas.confirmar_reserva().ejecutar(
        ConfirmarReservaDTO(
            id_reserva=reserva.id,
            referencia_pago="REF-TEST-SOCIAL",
        )
    )

    # Realizar check-in
    reserva_checkin = reservas.registrar_check_in().ejecutar(
        CheckInDTO(
            codigo_ticket=reserva.codigo_ticket,
            id_organizador=org.id,
        )
    )

    return {
        "organizador": org,
        "asistente": asistente,
        "experiencia": exp,
        "reserva": reserva_checkin,
    }


@pytest.mark.django_db
def test_flujo_resena_exitoso(cliente, escenario_completo):
    esc = escenario_completo
    reserva = esc["reserva"]
    asistente = esc["asistente"]
    org = esc["organizador"]
    exp = esc["experiencia"]

    # 1. Publicar reseña
    resp = cliente.post(
        f"{SOCIAL}/resenas",
        {
            "id_reserva": str(reserva.id),
            "id_usuario": str(asistente.id),
            "calificacion": 5,
            "comentario": "Increible cata!",
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    datos_resena = resp.data
    assert datos_resena["calificacion"] == 5
    assert datos_resena["comentario"] == "Increible cata!"

    # 2. Consultar reseña por ID
    resp_detalle = cliente.get(f"{SOCIAL}/resenas/{datos_resena['id']}")
    assert resp_detalle.status_code == status.HTTP_200_OK
    assert resp_detalle.data["id"] == datos_resena["id"]

    # 3. Consultar reseña asociada a la reserva
    resp_reserva = cliente.get(f"{SOCIAL}/reservas/{reserva.id}/resena")
    assert resp_reserva.status_code == status.HTTP_200_OK
    assert resp_reserva.data["id"] == datos_resena["id"]

    # 4. Listar reseñas de la experiencia
    resp_exp = cliente.get(f"{SOCIAL}/experiencias/{exp.id}/resenas")
    assert resp_exp.status_code == status.HTTP_200_OK
    assert len(resp_exp.data) == 1

    # 5. Metricas de la experiencia
    resp_met_exp = cliente.get(f"{SOCIAL}/experiencias/{exp.id}/metricas")
    assert resp_met_exp.status_code == status.HTTP_200_OK
    assert Decimal(resp_met_exp.data["calificacion_promedio"]) == Decimal("5.00")
    assert resp_met_exp.data["total_resenas"] == 1

    # 6. Listar reseñas del organizador
    resp_org = cliente.get(f"{SOCIAL}/organizadores/{org.id}/resenas")
    assert resp_org.status_code == status.HTTP_200_OK
    assert len(resp_org.data) == 1

    # 7. Metricas del organizador
    resp_met_org = cliente.get(f"{SOCIAL}/organizadores/{org.id}/metricas")
    assert resp_met_org.status_code == status.HTTP_200_OK
    assert Decimal(resp_met_org.data["calificacion_promedio"]) == Decimal("5.00")
    assert resp_met_org.data["total_resenas"] == 1

    # 8. Verificar que el modelo Organizador en Identidad actualizo calificacion_promedio
    org_actualizado = identidad.obtener_organizador().ejecutar(org.id)
    assert org_actualizado.calificacion_promedio == Decimal("5.00")


@pytest.mark.django_db
def test_resena_duplicada_retorna_409(cliente, escenario_completo):
    esc = escenario_completo
    reserva = esc["reserva"]
    asistente = esc["asistente"]

    # Primera reseña
    cliente.post(
        f"{SOCIAL}/resenas",
        {
            "id_reserva": str(reserva.id),
            "id_usuario": str(asistente.id),
            "calificacion": 4,
        },
        format="json",
    )

    # Segunda reseña para la misma reserva -> 409
    resp = cliente.post(
        f"{SOCIAL}/resenas",
        {
            "id_reserva": str(reserva.id),
            "id_usuario": str(asistente.id),
            "calificacion": 5,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.data["error"]["codigo"] == "resena_duplicada"


@pytest.mark.django_db
def test_resena_sin_checkin_retorna_409(cliente, escenario_completo):
    esc = escenario_completo
    exp = esc["experiencia"]

    otro_asistente = identidad.registrar_usuario().ejecutar(
        RegistrarUsuarioDTO(nombre="Ana Asistente", correo="ana.social@meetu2.co")
    )

    # Crear una reserva confirmada pero sin check-in
    otra_reserva = reservas.solicitar_reserva().ejecutar(
        SolicitarReservaDTO(
            id_usuario=otro_asistente.id,
            id_experiencia=exp.id,
            cantidad_cupos=1,
        )
    )
    reservas.confirmar_reserva().ejecutar(
        ConfirmarReservaDTO(
            id_reserva=otra_reserva.id,
            referencia_pago="REF-TEST-SIN-CHECKIN",
        )
    )

    resp = cliente.post(
        f"{SOCIAL}/resenas",
        {
            "id_reserva": str(otra_reserva.id),
            "id_usuario": str(otro_asistente.id),
            "calificacion": 5,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.data["error"]["codigo"] == "reserva_sin_check_in"


@pytest.mark.django_db
def test_resena_usuario_incorrecto_retorna_409(cliente, escenario_completo):
    esc = escenario_completo
    reserva = esc["reserva"]
    otro_usuario = uuid4()

    resp = cliente.post(
        f"{SOCIAL}/resenas",
        {
            "id_reserva": str(reserva.id),
            "id_usuario": str(otro_usuario),
            "calificacion": 5,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.data["error"]["codigo"] == "reserva_no_pertenece_a_usuario"


@pytest.mark.django_db
def test_resena_calificacion_invalida_retorna_400(cliente, escenario_completo):
    esc = escenario_completo
    reserva = esc["reserva"]
    asistente = esc["asistente"]

    resp = cliente.post(
        f"{SOCIAL}/resenas",
        {
            "id_reserva": str(reserva.id),
            "id_usuario": str(asistente.id),
            "calificacion": 10,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
