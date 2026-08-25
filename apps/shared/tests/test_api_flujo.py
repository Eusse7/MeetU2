"""
Prueba de integracion del flujo completo sobre HTTP.

Recorre el caso de uso de negocio de punta a punta -- registrar, verificar,
publicar, descubrir, reservar, confirmar -- y comprueba que cada error de
dominio llega al cliente con el codigo HTTP correcto (400 / 404 / 409).
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

IDENTIDAD = "/api/v1/identidad"
CATALOGO = "/api/v1/catalogo"
RESERVAS = "/api/v1/reservas"


@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def organizador_verificado(cliente):
    usuario = cliente.post(
        f"{IDENTIDAD}/usuarios",
        {"nombre": "Laura Host", "correo": "laura@meetu2.co"},
        format="json",
    ).data
    organizador = cliente.post(
        f"{IDENTIDAD}/usuarios/{usuario['id']}/organizador",
        {"nombre_comercial": "Cafe & Ritmo"},
        format="json",
    ).data
    cliente.patch(
        f"{IDENTIDAD}/organizadores/{organizador['id']}/verificacion",
        {"aprobado": True},
        format="json",
    )
    return organizador


@pytest.fixture
def ubicacion(cliente):
    return cliente.post(
        f"{CATALOGO}/ubicaciones",
        {
            "nombre": "Casa Rose",
            "direccion": "Cra 35 #8A-3",
            "ciudad": "Medellin",
            "latitud": 6.2087,
            "longitud": -75.5675,
            "aforo_maximo": 20,
        },
        format="json",
    ).data


@pytest.fixture
def experiencia(cliente, organizador_verificado, ubicacion):
    return cliente.post(
        f"{CATALOGO}/experiencias",
        {
            "id_organizador": organizador_verificado["id"],
            "id_ubicacion": ubicacion["id"],
            "titulo": "Cata de cafes de origen",
            "descripcion": "Cuatro origenes colombianos.",
            "fecha_hora": (timezone.now() + timedelta(days=5)).isoformat(),
            "precio": "45000.00",
            "cupo_maximo": 3,
        },
        format="json",
    ).data


@pytest.fixture
def asistente(cliente):
    return cliente.post(
        f"{IDENTIDAD}/usuarios",
        {"nombre": "Andres", "correo": "andres@meetu2.co"},
        format="json",
    ).data


pytestmark = pytest.mark.django_db


# --------------------------------------------------------------- Identidad
def test_registrar_usuario_devuelve_201(cliente):
    respuesta = cliente.post(
        f"{IDENTIDAD}/usuarios",
        {"nombre": "Andres", "correo": "andres@meetu2.co"},
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["tipo_perfil"] == "ASISTENTE"


def test_correo_invalido_devuelve_400(cliente):
    respuesta = cliente.post(
        f"{IDENTIDAD}/usuarios", {"nombre": "Andres", "correo": "no-es-correo"},
        format="json",
    )

    assert respuesta.status_code == 400


def test_correo_repetido_devuelve_409(cliente, asistente):
    respuesta = cliente.post(
        f"{IDENTIDAD}/usuarios",
        {"nombre": "Otro", "correo": "andres@meetu2.co"},
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "correo_ya_registrado"


def test_usuario_inexistente_devuelve_404(cliente):
    respuesta = cliente.get(
        f"{IDENTIDAD}/usuarios/11111111-1111-1111-1111-111111111111"
    )

    assert respuesta.status_code == 404
    assert respuesta.data["error"]["codigo"] == "usuario_no_encontrado"


# ---------------------------------------------------------------- Catalogo
def test_publicar_experiencia_devuelve_201(cliente, experiencia):
    assert experiencia["estado"] == "PUBLICADA"
    assert experiencia["cupo_disponible"] == 3


def test_organizador_sin_verificar_no_publica_409(cliente, ubicacion):
    usuario = cliente.post(
        f"{IDENTIDAD}/usuarios", {"nombre": "Pedro", "correo": "pedro@meetu2.co"},
        format="json",
    ).data
    organizador = cliente.post(
        f"{IDENTIDAD}/usuarios/{usuario['id']}/organizador",
        {"nombre_comercial": "Sin verificar"},
        format="json",
    ).data

    respuesta = cliente.post(
        f"{CATALOGO}/experiencias",
        {
            "id_organizador": organizador["id"],
            "id_ubicacion": ubicacion["id"],
            "titulo": "Experiencia no autorizada",
            "fecha_hora": (timezone.now() + timedelta(days=3)).isoformat(),
            "precio": "10000.00",
            "cupo_maximo": 5,
        },
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "organizador_no_autorizado"


def test_cupo_por_encima_del_aforo_devuelve_400(
    cliente, organizador_verificado, ubicacion
):
    respuesta = cliente.post(
        f"{CATALOGO}/experiencias",
        {
            "id_organizador": organizador_verificado["id"],
            "id_ubicacion": ubicacion["id"],
            "titulo": "Fiesta multitudinaria",
            "fecha_hora": (timezone.now() + timedelta(days=3)).isoformat(),
            "precio": "10000.00",
            "cupo_maximo": 500,
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "aforo_excedido"


def test_buscar_experiencias_filtra_por_ciudad(cliente, experiencia):
    encontradas = cliente.get(f"{CATALOGO}/experiencias?ciudad=Medellin").data
    vacias = cliente.get(f"{CATALOGO}/experiencias?ciudad=Bogota").data

    assert len(encontradas) == 1
    assert vacias == []


# ---------------------------------------------------------------- Reservas
def test_flujo_reservar_y_confirmar(cliente, asistente, experiencia):
    creada = cliente.post(
        f"{RESERVAS}/reservas",
        {
            "id_usuario": asistente["id"],
            "id_experiencia": experiencia["id"],
            "cantidad_cupos": 2,
        },
        format="json",
    )
    assert creada.status_code == 201
    assert creada.data["estado"] == "PENDIENTE_PAGO"
    assert Decimal(creada.data["monto_total"]) == Decimal("90000.00")

    # El cupo quedo retenido en el catalogo.
    detalle = cliente.get(f"{CATALOGO}/experiencias/{experiencia['id']}").data
    assert detalle["cupo_disponible"] == 1

    confirmada = cliente.post(
        f"{RESERVAS}/reservas/{creada.data['id']}/confirmacion",
        {"referencia_pago": "TX-123"},
        format="json",
    )
    assert confirmada.status_code == 200
    assert confirmada.data["estado"] == "CONFIRMADA"


def test_reservar_mas_cupos_de_los_disponibles_devuelve_409(
    cliente, asistente, experiencia
):
    respuesta = cliente.post(
        f"{RESERVAS}/reservas",
        {
            "id_usuario": asistente["id"],
            "id_experiencia": experiencia["id"],
            "cantidad_cupos": 5,
        },
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "cupo_insuficiente"


def test_reservar_dos_veces_devuelve_409(cliente, asistente, experiencia):
    cuerpo = {"id_usuario": asistente["id"], "id_experiencia": experiencia["id"]}
    cliente.post(f"{RESERVAS}/reservas", cuerpo, format="json")

    respuesta = cliente.post(f"{RESERVAS}/reservas", cuerpo, format="json")

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "reserva_duplicada"


def test_cancelar_devuelve_el_cupo(cliente, asistente, experiencia):
    reserva = cliente.post(
        f"{RESERVAS}/reservas",
        {
            "id_usuario": asistente["id"],
            "id_experiencia": experiencia["id"],
            "cantidad_cupos": 3,
        },
        format="json",
    ).data
    agotada = cliente.get(f"{CATALOGO}/experiencias/{experiencia['id']}").data
    assert agotada["estado"] == "AGOTADA"

    cancelada = cliente.post(
        f"{RESERVAS}/reservas/{reserva['id']}/cancelacion",
        {"id_usuario": asistente["id"], "motivo": "cambio de planes"},
        format="json",
    )

    assert cancelada.status_code == 200
    repuesta = cliente.get(f"{CATALOGO}/experiencias/{experiencia['id']}").data
    assert repuesta["cupo_disponible"] == 3
    assert repuesta["estado"] == "PUBLICADA"


def test_confirmar_una_reserva_cancelada_devuelve_409(
    cliente, asistente, experiencia
):
    reserva = cliente.post(
        f"{RESERVAS}/reservas",
        {"id_usuario": asistente["id"], "id_experiencia": experiencia["id"]},
        format="json",
    ).data
    cliente.post(
        f"{RESERVAS}/reservas/{reserva['id']}/cancelacion",
        {"id_usuario": asistente["id"]},
        format="json",
    )

    respuesta = cliente.post(
        f"{RESERVAS}/reservas/{reserva['id']}/confirmacion", {}, format="json"
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "transicion_reserva_invalida"


def test_ticket_inexistente_en_check_in_devuelve_404(
    cliente, organizador_verificado
):
    respuesta = cliente.post(
        f"{RESERVAS}/reservas/check-in",
        {"codigo_ticket": "NOEXISTE", "id_organizador": organizador_verificado["id"]},
        format="json",
    )

    assert respuesta.status_code == 404
    assert respuesta.data["error"]["codigo"] == "codigo_ticket_invalido"


def test_mis_reservas_incluye_el_titulo_de_la_experiencia(
    cliente, asistente, experiencia
):
    cliente.post(
        f"{RESERVAS}/reservas",
        {"id_usuario": asistente["id"], "id_experiencia": experiencia["id"]},
        format="json",
    )

    respuesta = cliente.get(f"{RESERVAS}/usuarios/{asistente['id']}/reservas")

    assert respuesta.status_code == 200
    assert respuesta.data[0]["experiencia_titulo"] == "Cata de cafes de origen"


# ---------------------------------------------------------- Recomendaciones
def test_las_recomendaciones_priorizan_las_categorias_del_usuario(
    cliente, asistente, organizador_verificado, ubicacion
):
    gastronomia = cliente.post(
        f"{CATALOGO}/categorias", {"nombre": "Gastronomia"}, format="json"
    ).data
    cliente.post(f"{CATALOGO}/categorias", {"nombre": "Aire libre"}, format="json")

    def publicar(titulo, categorias, dias):
        return cliente.post(
            f"{CATALOGO}/experiencias",
            {
                "id_organizador": organizador_verificado["id"],
                "id_ubicacion": ubicacion["id"],
                "titulo": titulo,
                "fecha_hora": (timezone.now() + timedelta(days=dias)).isoformat(),
                "precio": "20000.00",
                "cupo_maximo": 10,
                "categorias": categorias,
            },
            format="json",
        ).data

    publicar("Caminata de montana", [], 2)
    publicar("Cata de cafes de origen", [gastronomia["id"]], 9)

    cliente.post(
        f"{IDENTIDAD}/usuarios/{asistente['id']}/intereses",
        {"id_categoria": gastronomia["id"], "nivel_afinidad": 5},
        format="json",
    )

    respuesta = cliente.get(
        f"{CATALOGO}/usuarios/{asistente['id']}/recomendaciones"
    )

    assert respuesta.status_code == 200
    # La afin va primero aunque su fecha sea posterior.
    assert respuesta.data[0]["experiencia"]["titulo"] == "Cata de cafes de origen"
    assert respuesta.data[0]["afinidad"] == 1.0
    assert respuesta.data[1]["afinidad"] == 0.0
