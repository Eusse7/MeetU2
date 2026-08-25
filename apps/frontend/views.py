"""
Vistas del front.

Solo renderizan plantillas: no consultan servicios ni el ORM. Todo el trafico
de datos ocurre en el navegador contra /api/v1, de modo que la capa de
presentacion es intercambiable (una SPA, una app movil) sin tocar el backend.
"""
from django.views.generic import TemplateView


class CatalogoView(TemplateView):
    template_name = "frontend/catalogo.html"


class ReservasView(TemplateView):
    template_name = "frontend/reservas.html"


class OrganizadorView(TemplateView):
    template_name = "frontend/organizador.html"
