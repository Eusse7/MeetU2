"""Pruebas unitarias y de integracion del microservicio Notificaciones."""
import uuid
import pytest

from notificaciones_service import create_app


@pytest.fixture
def app():
    app = create_app(database_url="sqlite:///:memory:")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_salud(client):
    resp = client.get("/api/v2/notificaciones/salud")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["servicio"] == "notificaciones"
    assert "email" in data["canales_soportados"]


def test_enviar_notificacion_email_exitoso(client):
    usuario_id = str(uuid.uuid4())
    payload = {
        "usuario_id": usuario_id,
        "canal": "email",
        "destinatario": "asistente@example.com",
        "asunto": "Reserva confirmada en MeetU2",
        "mensaje": "Tu cupo ha sido reservado con exito.",
        "metadata": {"reserva_id": str(uuid.uuid4())},
    }
    resp = client.post("/api/v2/notificaciones/enviar", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["estado"] == "ENVIADA"
    assert data["canal"] == "email"
    assert data["destinatario"] == payload["destinatario"]


def test_enviar_notificacion_faltan_campos(client):
    payload = {
        "usuario_id": str(uuid.uuid4()),
        "canal": "sms",
    }
    resp = client.post("/api/v2/notificaciones/enviar", json=payload)
    assert resp.status_code == 400
    assert "es obligatorio" in resp.get_json()["error"]


def test_consultar_historial_usuario(client):
    usuario_id = str(uuid.uuid4())
    for i in range(2):
        payload = {
            "usuario_id": usuario_id,
            "canal": "push",
            "destinatario": f"device_token_{i}",
            "asunto": f"Recordatorio {i}",
            "mensaje": f"Tu evento comienza pronto {i}",
        }
        resp = client.post("/api/v2/notificaciones/enviar", json=payload)
        assert resp.status_code == 201

    resp_hist = client.get(f"/api/v2/notificaciones/historial/{usuario_id}")
    assert resp_hist.status_code == 200
    historial = resp_hist.get_json()
    assert len(historial) == 2
    assert historial[0]["usuario_id"] == usuario_id
