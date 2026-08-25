from django.urls import path

from apps.frontend.views import CatalogoView, OrganizadorView, ReservasView

app_name = "frontend"

urlpatterns = [
    path("", CatalogoView.as_view(), name="catalogo"),
    path("mis-reservas/", ReservasView.as_view(), name="reservas"),
    path("organizador/", OrganizadorView.as_view(), name="organizador"),
]
