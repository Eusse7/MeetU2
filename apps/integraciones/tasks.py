"""
Tareas asíncronas de integración y reportes de fondo con Celery.
Cumple el requerimiento de Message Broker (Redis/Celery) para procesos de fondo.
"""
import logging
import time
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("meetu2.integraciones.tasks")


@shared_task(name="apps.integraciones.tasks.generar_reporte_sistema_async", bind=True)
def generar_reporte_sistema_async(self, correo_solicitante: str = "admin@meetu2.co"):
    """
    Tarea de larga duración ejecutada en worker de Celery.
    Genera un informe consolidado de auditoría, ocupación y ventas.
    """
    logger.info("Iniciando generación de reporte asíncrono para %s", correo_solicitante)
    
    # Simula proceso de cómputo y consolidación de datos
    time.sleep(1)

    from apps.catalogo.domain.models import Experiencia
    from apps.reservas.domain.models import Reserva
    from apps.social.domain.models import Resena

    total_experiencias = Experiencia.objects.count()
    experiencias_publicadas = Experiencia.objects.filter(estado="PUBLICADA").count()
    total_reservas = Reserva.objects.count()
    reservas_confirmadas = Reserva.objects.filter(estado__in=["CONFIRMADA", "CHECK_IN"]).count()
    total_resenas = Resena.objects.count()

    ahora = timezone.now()

    reporte = {
        "generado_en": ahora.isoformat(),
        "solicitante": correo_solicitante,
        "metricas": {
            "total_experiencias": total_experiencias,
            "experiencias_activas": experiencias_publicadas,
            "total_reservas": total_reservas,
            "reservas_confirmadas_o_checkin": reservas_confirmadas,
            "total_resenas_comunidad": total_resenas,
        },
        "estado": "COMPLETADO",
        "mensaje": "Reporte consolidado generado con éxito por el worker Celery.",
    }

    logger.info("Reporte asíncrono completado para %s", correo_solicitante)
    return reporte
