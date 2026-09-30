"""
Pruebas HTTP del microservicio: JSON de entrada, JSON de salida y errores
estructurados 400/402/404/409/500.
"""
from uuid import uuid4

from tests.conftest import ID_ORGANIZADOR, ID_USUARIO


def pagar(client, reserva, **extra):
    cuerpo = {
        "id_reserva": str(reserva.id),
        "id_usuario": str(ID_USUARIO),
        "medio_pago": "TARJETA",
        **extra,
    }
    return client.post("/api/v2/pagos", json=cuerpo)


def test_salud(client):
    r = client.get("/api/v2/pagos/salud")
    assert r.status_code == 200
    assert r.get_json()["servicio"] == "meetu2-pagos"


# ----------------------------------------------------------------- cobro
def test_pago_aprobado_confirma_la_reserva_en_el_monolito(client, monolito):
    reserva = monolito.agregar()
    r = pagar(client, reserva)

    assert r.status_code == 201
    cuerpo = r.get_json()
    assert cuerpo["estado"] == "APROBADO"
    assert cuerpo["monto"] == "90000.00"
    assert cuerpo["neto_organizador"] == "81000.00"
    assert cuerpo["reserva_confirmada"] is True
    assert monolito.confirmaciones == [(reserva.id, cuerpo["referencia"])]


def test_pago_rechazado_es_402_y_queda_registrado(client, monolito, repo):
    reserva = monolito.agregar()
    r = pagar(client, reserva, token_pago="tok_rechazada")

    assert r.status_code == 402
    assert r.get_json()["error"]["codigo"] == "pago_rechazado"
    assert monolito.confirmaciones == []
    assert repo.contar() == 1
    # Tras un rechazo se puede reintentar con otro medio.
    assert pagar(client, reserva).status_code == 201


def test_pagar_dos_veces_es_409(client, monolito):
    reserva = monolito.agregar()
    pagar(client, reserva)
    r = pagar(client, reserva)
    assert r.status_code == 409
    assert r.get_json()["error"]["codigo"] == "pago_duplicado"


def test_solo_el_titular_puede_pagar(client, monolito):
    reserva = monolito.agregar()
    r = pagar(client, reserva, id_usuario=str(uuid4()))
    assert r.status_code == 409
    assert r.get_json()["error"]["codigo"] == "usuario_no_autorizado"


def test_reserva_inexistente_es_404(client):
    r = client.post(
        "/api/v2/pagos",
        json={"id_reserva": str(uuid4()), "id_usuario": str(ID_USUARIO),
              "medio_pago": "PSE"},
    )
    assert r.status_code == 404
    assert r.get_json()["error"]["codigo"] == "reserva_no_encontrada"


def test_reserva_no_pendiente_es_409(client, monolito):
    reserva = monolito.agregar(estado="CANCELADA")
    r = pagar(client, reserva)
    assert r.status_code == 409
    assert r.get_json()["error"]["codigo"] == "reserva_no_pagable"


def test_si_el_monolito_rechaza_la_confirmacion_se_compensa(client, monolito, repo):
    reserva = monolito.agregar()
    monolito.rechazar_confirmacion = True

    r = pagar(client, reserva)

    assert r.status_code == 409
    pago = repo.listar(id_reserva=reserva.id)[0]
    assert pago.estado == "REEMBOLSADO"
    assert pago.monto_reembolsado == pago.monto


# ------------------------------------------------------ validacion de forma
def test_cuerpo_que_no_es_json_es_400(client):
    r = client.post("/api/v2/pagos", data="hola", content_type="text/plain")
    assert r.status_code == 400
    assert r.get_json()["error"]["codigo"] == "json_invalido"


def test_campo_faltante_es_400(client):
    r = client.post("/api/v2/pagos", json={"id_usuario": str(ID_USUARIO)})
    assert r.status_code == 400
    assert r.get_json()["error"]["detalle"] == {"campo": "id_reserva"}


def test_uuid_invalido_es_400(client):
    r = client.post(
        "/api/v2/pagos",
        json={"id_reserva": "no-uuid", "id_usuario": str(ID_USUARIO), "medio_pago": "PSE"},
    )
    assert r.status_code == 400


def test_medio_invalido_es_400(client, monolito):
    r = pagar(client, monolito.agregar(), medio_pago="EFECTIVO")
    assert r.status_code == 400
    assert r.get_json()["error"]["codigo"] == "medio_pago_invalido"


def test_ruta_inexistente_devuelve_json(client):
    r = client.get("/api/v2/pagos/no/existe/aqui")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_metodo_no_permitido_devuelve_json(client):
    r = client.delete("/api/v2/pagos")
    assert r.status_code == 405
    assert r.get_json()["error"]["codigo"] == "method_not_allowed"


def test_error_inesperado_es_500_estructurado(app, client, monkeypatch):
    def explota(*_a, **_k):
        raise RuntimeError("detalle interno que no debe filtrarse")

    monkeypatch.setattr(app.extensions["pagos.repositorio"], "listar", explota)
    r = client.get("/api/v2/pagos")
    assert r.status_code == 500
    assert r.get_json()["error"]["codigo"] == "error_interno"
    assert "detalle interno" not in r.get_data(as_text=True)


# --------------------------------------------------------------- consultas
def test_consultar_por_id_y_por_referencia(client, monolito):
    creado = pagar(client, monolito.agregar()).get_json()

    por_id = client.get(f"/api/v2/pagos/{creado['id']}")
    por_ref = client.get(f"/api/v2/pagos/referencias/{creado['referencia']}")

    assert por_id.status_code == por_ref.status_code == 200
    assert por_id.get_json()["id"] == por_ref.get_json()["id"] == creado["id"]


def test_pago_inexistente_es_404(client):
    assert client.get(f"/api/v2/pagos/{uuid4()}").status_code == 404
    assert client.get("/api/v2/pagos/referencias/PAG-NOEXISTE").status_code == 404


def test_listar_filtra_por_reserva(client, monolito):
    a, b = monolito.agregar(), monolito.agregar()
    pagar(client, a)
    pagar(client, b)
    r = client.get(f"/api/v2/pagos?id_reserva={a.id}")
    assert [p["id_reserva"] for p in r.get_json()] == [str(a.id)]


# -------------------------------------------------------------- reembolsos
def test_reembolso_parcial_segun_la_politica_del_monolito(client, monolito):
    reserva = monolito.agregar()
    pagar(client, reserva)
    monolito.cambiar(reserva.id, estado="CANCELADA", monto_reembolsado=reserva.monto_total / 2)

    r = client.post("/api/v2/pagos/reembolsos", json={"id_reserva": str(reserva.id)})

    assert r.status_code == 200
    assert r.get_json()["estado"] == "REEMBOLSO_PARCIAL"
    assert r.get_json()["monto_reembolsado"] == "45000.00"


def test_reembolso_de_reserva_no_cancelada_es_409(client, monolito):
    reserva = monolito.agregar()
    pagar(client, reserva)
    r = client.post("/api/v2/pagos/reembolsos", json={"id_reserva": str(reserva.id)})
    assert r.status_code == 409


def test_cancelacion_sin_derecho_a_reembolso_es_409(client, monolito):
    reserva = monolito.agregar()
    pagar(client, reserva)
    monolito.cambiar(reserva.id, estado="CANCELADA")
    r = client.post("/api/v2/pagos/reembolsos", json={"id_reserva": str(reserva.id)})
    assert r.status_code == 409
    assert r.get_json()["error"]["codigo"] == "sin_reembolso"


def test_no_se_reembolsa_dos_veces(client, monolito):
    reserva = monolito.agregar()
    pagar(client, reserva)
    monolito.cambiar(reserva.id, estado="CANCELADA", monto_reembolsado=reserva.monto_total)
    assert client.post("/api/v2/pagos/reembolsos", json={"id_reserva": str(reserva.id)}).status_code == 200
    assert client.post("/api/v2/pagos/reembolsos", json={"id_reserva": str(reserva.id)}).status_code == 409


# ------------------------------------------------------------ liquidacion
def test_liquidacion_del_organizador(client, monolito):
    pagar(client, monolito.agregar(monto="100000.00", comision="10000.00"))
    pagar(client, monolito.agregar(monto="50000.00", comision="5000.00"))
    rechazada = monolito.agregar()
    pagar(client, rechazada, token_pago="tok_rechazada")

    r = client.get(f"/api/v2/pagos/organizadores/{ID_ORGANIZADOR}/liquidacion")

    assert r.status_code == 200
    cuerpo = r.get_json()
    assert cuerpo["pagos_considerados"] == 2
    assert cuerpo["total_cobrado"] == "150000.00"
    assert cuerpo["comision_plataforma"] == "15000.00"
    assert cuerpo["neto_a_desembolsar"] == "135000.00"
