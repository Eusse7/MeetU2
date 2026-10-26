"""Pruebas unitarias y de integracion del microservicio Social."""
import uuid
import pytest

from social_service import create_app
from social_service.domain import EstadoResena, Resena


@pytest.fixture
def app():
    app = create_app(database_url="sqlite:///:memory:")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_salud(client):
    resp = client.get("/api/v2/social/salud")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["servicio"] == "social"
    assert data["status"] == "ok"


def test_crear_resena_exitoso(client):
    payload = {
        "reserva_id": str(uuid.uuid4()),
        "usuario_id": str(uuid.uuid4()),
        "experiencia_id": str(uuid.uuid4()),
        "organizador_id": str(uuid.uuid4()),
        "calificacion": 5,
        "comentario": "¡Excelente experiencia y gran anfitrión!",
        "verificar_checkin": False,
    }
    resp = client.post("/api/v2/social/resenas", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["calificacion"] == 5
    assert data["comentario"] == payload["comentario"]
    assert data["reserva_id"] == payload["reserva_id"]


def test_crear_resena_duplicada_para_misma_reserva(client):
    reserva_id = str(uuid.uuid4())
    payload = {
        "reserva_id": reserva_id,
        "usuario_id": str(uuid.uuid4()),
        "experiencia_id": str(uuid.uuid4()),
        "organizador_id": str(uuid.uuid4()),
        "calificacion": 4,
        "verificar_checkin": False,
    }
    resp1 = client.post("/api/v2/social/resenas", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v2/social/resenas", json=payload)
    assert resp2.status_code == 409
    assert "Ya existe una reseña" in resp2.get_json()["error"]


def test_crear_resena_calificacion_invalida(client):
    payload = {
        "reserva_id": str(uuid.uuid4()),
        "usuario_id": str(uuid.uuid4()),
        "experiencia_id": str(uuid.uuid4()),
        "organizador_id": str(uuid.uuid4()),
        "calificacion": 6,  # Invalida (>5)
        "verificar_checkin": False,
    }
    resp = client.post("/api/v2/social/resenas", json=payload)
    assert resp.status_code == 400
    assert "Debe estar entre 1 y 5" in resp.get_json()["error"]


def test_calcular_reputacion_organizador(client):
    organizador_id = str(uuid.uuid4())
    # Dos reseñas para el mismo organizador: 5 y 3 (promedio 4.0)
    for calif in [5, 3]:
        payload = {
            "reserva_id": str(uuid.uuid4()),
            "usuario_id": str(uuid.uuid4()),
            "experiencia_id": str(uuid.uuid4()),
            "organizador_id": organizador_id,
            "calificacion": calif,
            "verificar_checkin": False,
        }
        resp = client.post("/api/v2/social/resenas", json=payload)
        assert resp.status_code == 201

    resp_rep = client.get(f"/api/v2/social/organizadores/{organizador_id}/reputacion")
    assert resp_rep.status_code == 200
    data = resp_rep.get_json()
    assert data["total_resenas"] == 2
    assert data["promedio"] == 4.0


def test_listar_resenas_experiencia(client):
    exp_id = str(uuid.uuid4())
    payload = {
        "reserva_id": str(uuid.uuid4()),
        "usuario_id": str(uuid.uuid4()),
        "experiencia_id": exp_id,
        "organizador_id": str(uuid.uuid4()),
        "calificacion": 5,
        "comentario": "Gran tarde al aire libre",
        "verificar_checkin": False,
    }
    client.post("/api/v2/social/resenas", json=payload)

    resp = client.get(f"/api/v2/social/resenas?experiencia_id={exp_id}")
    assert resp.status_code == 200
    resenas = resp.get_json()
    assert len(resenas) == 1
    assert resenas[0]["experiencia_id"] == exp_id
