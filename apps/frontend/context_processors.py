"""Banderas de configuracion que el front necesita conocer."""
from django.conf import settings


def feature_flags(request):
    return {"pagos_v2_habilitado": settings.PAGOS_V2_HABILITADO}
