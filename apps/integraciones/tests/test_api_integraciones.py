"""Pruebas de los endpoints REST de integración (Servicio a Proveer, a Consumir, Terceros y Celery)."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient


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
def test_endpoint_reporte_asincrono_celery(settings):
    # En entorno de pruebas activamos modo eager para que Celery ejecute de inmediato
    settings.CELERY_TASK_ALWAYS_EAGER = True
    client = APIClient()

    resp_post = client.post(
        "/api/v1/integracion/reportes/asincrono/",
        {"correo": "auditor@meetu2.co"},
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
