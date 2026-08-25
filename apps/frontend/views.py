from django.views.generic import TemplateView


class CatalogoView(TemplateView):
    template_name = "frontend/catalogo.html"


class OrganizadorView(TemplateView):
    template_name = "frontend/organizador.html"