"""Pruebas del patron Factory de notificaciones."""
import pytest
from django.test import override_settings

from apps.notificaciones.application.ports import Notificacion, NotificadorPort
from apps.notificaciones.infrastructure.canales.consola import NotificadorConsola
from apps.notificaciones.infrastructure.canales.email import NotificadorEmail
from apps.notificaciones.infrastructure.canales.push import NotificadorPush
from apps.notificaciones.infrastructure.factories import (
    CanalNoSoportado,
    NotificadorFactory,
)


@pytest.mark.parametrize(
    "canal,clase",
    [
        ("consola", NotificadorConsola),
        ("email", NotificadorEmail),
        ("push", NotificadorPush),
    ],
)
def test_crea_el_canal_pedido(canal, clase):
    assert isinstance(NotificadorFactory.crear(canal), clase)


def test_el_nombre_del_canal_es_insensible_a_mayusculas():
    assert isinstance(NotificadorFactory.crear("EMAIL"), NotificadorEmail)


@override_settings(CANAL_NOTIFICACION_DEFECTO="push")
def test_sin_argumento_usa_el_canal_configurado():
    assert isinstance(NotificadorFactory.crear(), NotificadorPush)


def test_un_canal_desconocido_falla_ruidosamente():
    with pytest.raises(CanalNoSoportado) as exc:
        NotificadorFactory.crear("paloma-mensajera")

    # El mensaje debe orientar a quien configuro mal el entorno.
    assert "consola" in str(exc.value)


def test_se_puede_registrar_un_canal_nuevo_sin_tocar_la_factory():
    """Principio Abierto/Cerrado: extender sin modificar."""

    class NotificadorWhatsApp(NotificadorPort):
        nombre = "whatsapp"

        def enviar(self, notificacion: Notificacion) -> bool:
            return True

    NotificadorFactory.registrar(NotificadorWhatsApp)
    try:
        assert isinstance(NotificadorFactory.crear("whatsapp"), NotificadorWhatsApp)
        assert "whatsapp" in NotificadorFactory.canales_disponibles()
    finally:
        NotificadorFactory._registro.pop("whatsapp", None)


def test_todos_los_canales_cumplen_el_puerto():
    for canal in NotificadorFactory.canales_disponibles():
        assert isinstance(NotificadorFactory.crear(canal), NotificadorPort)
