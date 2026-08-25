from django.urls import path

from .views import CatalogoView, OrganizadorView

app_name = "frontend"

urlpatterns = [
    path("", CatalogoView.as_view(), name="catalogo"),
    path("organizador/", OrganizadorView.as_view(), name="organizador"),
]