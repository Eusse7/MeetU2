"""Pruebas de los endpoints REST de integración (Servicio a Proveer, a Consumir, Terceros y Celery)."""
from uuid import uuid4

import pytest
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient

from apps.integraciones.models import ReservaHotel


@pytest.mark.django_db
def test_endpoint_servicio_a_proveer_retorna_catalogo_json():
    client = APIClient()
    resp = client.get("/api/v1/integracion/experiencias-publicas/")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["plataforma"] == "MeetU2"
    assert "experiencias" in data
    assert isinstance(data["experiencias"], list)


@pytest.mark.django_db
def test_endpoint_servicio_a_consumir_retorna_planes_aliados():
    client = APIClient()
    resp = client.get("/api/v1/integracion/aliados/planes/")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "planes" in data
    assert len(data["planes"]) >= 1
    hotel = data["planes"][0]
    assert "titulo" in hotel
    assert "precio" in hotel
    assert "amenidades" in hotel
    assert "estrellas" in hotel


@pytest.mark.django_db
def test_endpoint_partner_hotels_y_simulador():
    client = APIClient()
    # Endpoint de la API del socio hotelero
    resp = client.get("/api/v1/integracion/partner/hotels/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "hotelMDJ" in data["servicio"]
    assert "hoteles" in data
    assert len(data["hoteles"]) >= 1
    assert data["hoteles"][0]["precio_noche"] > 0

    # Alias compatible
    resp_alias = client.get("/api/v1/integracion/simulador/hoteles/")
    assert resp_alias.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_endpoint_reservar_hotel_aliado_y_aislamiento_entre_usuarios():
    client = APIClient()
    user_a = uuid4()
    user_b = uuid4()

    payload_a = {
        "usuario_id": str(user_a),
        "hotel_id": "hotel-poblado-01",
        "nombre_hotel": "Hotel Boutique & Spa El Poblado",
        "tipo_alojamiento": "Suite Deluxe con Balcón",
        "ciudad": "Medellín",
        "checkin": "2026-11-20",
        "checkout": "2026-11-22",
        "habitaciones": 1,
        "huesped_nombre": "Andrés Asistente",
        "huesped_correo": "andres@meetu2.co",
        "precio_noche": 220000,
    }
    resp = client.post(
        "/api/v1/integracion/aliados/hoteles/reserva/",
        payload_a,
        format="json",
    )

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["status"] == "confirmada"
    assert data["codigo_reserva"].startswith("MDJ-")
    assert data["hotel"] == "Hotel Boutique & Spa El Poblado"
    assert data["noches"] == 2
    assert data["monto_total"] == 440000.0

    codigo = data["codigo_reserva"]

    # Verificar que se refleja en la base de datos
    assert ReservaHotel.objects.filter(codigo_reserva=codigo, usuario_id=user_a).exists()

    # Usuario A consulta sus reservas -> La encuentra
    resp_a = client.get(f"/api/v1/integracion/aliados/hoteles/mis-reservas/?usuario_id={user_a}")
    assert resp_a.status_code == status.HTTP_200_OK
    reservas_a = resp_a.json()
    assert len(reservas_a) == 1
    assert reservas_a[0]["codigo_reserva"] == codigo

    # Usuario B consulta sus reservas -> Lista vacía (NO ve la reserva de A)
    resp_b = client.get(f"/api/v1/integracion/aliados/hoteles/mis-reservas/?usuario_id={user_b}")
    assert resp_b.status_code == status.HTTP_200_OK
    assert resp_b.json() == []

    # Consulta sin usuario -> Lista vacía (protección contra fuga de datos)
    resp_anon = client.get("/api/v1/integracion/aliados/hoteles/mis-reservas/")
    assert resp_anon.status_code == status.HTTP_200_OK
    assert resp_anon.json() == []

    # Cancelar la reserva de hotel
    resp_cancel = client.post(
        f"/api/v1/integracion/aliados/hoteles/reservas/{codigo}/cancelar/"
    )
    assert resp_cancel.status_code == status.HTTP_200_OK
    assert resp_cancel.json()["estado"] == "CANCELADA"

    reserva_db = ReservaHotel.objects.get(codigo_reserva=codigo)
    assert reserva_db.estado == "CANCELADA"


@pytest.mark.django_db
def test_endpoint_clima_api_terceros():
    client = APIClient()
    resp = client.get("/api/v1/integracion/clima/?ciudad=Medellin")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["ciudad"] == "Medellin"
    assert "temperatura_c" in data
    assert "icono" in data
    assert "proveedor" in data


@pytest.mark.django_db
def test_endpoint_reporte_asincrono_celery_y_envio_correo(settings):
    # En entorno de pruebas activamos modo eager para que Celery ejecute de inmediato
    settings.CELERY_TASK_ALWAYS_EAGER = True
    mail.outbox.clear()
    client = APIClient()

    correo_destino = "auditor@meetu2.co"
    resp_post = client.post(
        "/api/v1/integracion/reportes/asincrono/",
        {"correo": correo_destino},
        format="json",
    )
    assert resp_post.status_code == status.HTTP_202_ACCEPTED
    task_id = resp_post.json()["task_id"]
    assert task_id

    # Consultar estado
    resp_get = client.get(f"/api/v1/integracion/reportes/asincrono/{task_id}/")
    assert resp_get.status_code == status.HTTP_200_OK
    data_get = resp_get.json()
    assert data_get["task_id"] == task_id

    # Verificar que el correo realmente se envió por Django mailer
    assert len(mail.outbox) >= 1
    email_enviado = mail.outbox[-1]
    assert correo_destino in email_enviado.to
    assert "Reporte Consolidado" in email_enviado.subject
    assert "MÉTRICAS CONSOLIDADAS" in email_enviado.body
