"""Pruebas unitarias y de integracion del microservicio Catalogo."""
import uuid
import pytest

from catalogo_service import create_app


@pytest.fixture
def app():
    app = create_app(database_url="sqlite:///:memory:")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_salud(client):
    resp = client.get("/api/v2/catalogo/salud")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["servicio"] == "catalogo"


def test_crear_categoria_y_listar(client):
    payload = {"nombre": "Gastronomía Social", "descripcion": "Cenas y catas"}
    resp = client.post("/api/v2/catalogo/categorias", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["slug"] == "gastronomia-social"

    resp_list = client.get("/api/v2/catalogo/categorias")
    assert resp_list.status_code == 200
    assert len(resp_list.get_json()) == 1


def test_crear_ubicacion_y_experiencia_exitoso(client):
    # 1. Crear ubicacion con aforo 50
    ubi_payload = {
        "nombre": "Terraza Usaquén",
        "direccion": "Calle 119 # 6-20",
        "ciudad": "Bogota",
        "latitud": 4.69,
        "longitud": -74.03,
        "aforo_maximo": 50,
    }
    ubi_resp = client.post("/api/v2/catalogo/ubicaciones", json=ubi_payload)
    assert ubi_resp.status_code == 201
    ubi_id = ubi_resp.get_json()["id"]

    # 2. Crear categoria
    cat_resp = client.post("/api/v2/catalogo/categorias", json={"nombre": "Café y Arte"})
    assert cat_resp.status_code == 201
    cat_id = cat_resp.get_json()["id"]

    # 3. Crear experiencia con cupo 20 (menor al aforo)
    exp_payload = {
        "organizador_id": str(uuid.uuid4()),
        "categoria_id": cat_id,
        "ubicacion_id": ubi_id,
        "titulo": "Cata de Café y Pintura",
        "descripcion": "Tarde creativa",
        "precio_cop": 85000,
        "cupo_maximo": 20,
    }
    exp_resp = client.post("/api/v2/catalogo/experiencias", json=exp_payload)
    assert exp_resp.status_code == 201
    exp_data = exp_resp.get_json()
    assert exp_data["titulo"] == "Cata de Café y Pintura"
    assert exp_data["cupos_disponibles"] == 20


def test_crear_experiencia_excede_aforo(client):
    ubi_resp = client.post("/api/v2/catalogo/ubicaciones", json={
        "nombre": "Sala Pequeña",
        "direccion": "Cra 7 # 45",
        "ciudad": "Bogota",
        "latitud": 4.62,
        "longitud": -74.06,
        "aforo_maximo": 10,
    })
    ubi_id = ubi_resp.get_json()["id"]

    cat_resp = client.post("/api/v2/catalogo/categorias", json={"nombre": "Música"})
    cat_id = cat_resp.get_json()["id"]

    # Cupo 25 excede aforo 10
    exp_payload = {
        "organizador_id": str(uuid.uuid4()),
        "categoria_id": cat_id,
        "ubicacion_id": ubi_id,
        "titulo": "Concierto Acústico",
        "precio_cop": 50000,
        "cupo_maximo": 25,
    }
    exp_resp = client.post("/api/v2/catalogo/experiencias", json=exp_payload)
    assert exp_resp.status_code == 400
    assert "excede el aforo" in exp_resp.get_json()["error"]
