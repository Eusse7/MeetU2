"""Pruebas de internacionalización (i18n) con gettext."""
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework.test import APIClient


def test_traduccion_gettext():
    with translation.override("es"):
        assert _("Explorar") == "Explorar"
        assert _("Cómo funciona") == "Cómo funciona"

    with translation.override("en"):
        assert _("Explorar") == "Explore"
        assert _("Cómo funciona") == "How it works"
        assert _("Mis reservas") == "My bookings"
        assert _("Iniciar sesión") == "Sign in"


def test_endpoint_set_language():
    client = APIClient()
    resp = client.post("/i18n/setlang/", {"language": "en", "next": "/"})
    # set_language responde 302 hacia 'next' y setea la cookie django_language
    assert resp.status_code == 302
    assert resp.cookies.get("django_language").value == "en"
