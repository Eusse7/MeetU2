from django.contrib import admin

from apps.social.domain.models import Resena


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reserva_id",
        "usuario_id",
        "experiencia_id",
        "organizador_id",
        "calificacion",
        "estado",
        "creado_en",
    )
    list_filter = ("estado", "calificacion")
    search_fields = ("reserva_id", "usuario_id", "experiencia_id", "organizador_id")
