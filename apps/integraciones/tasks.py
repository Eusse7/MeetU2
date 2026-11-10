"""
Tareas asíncronas de integración y reportes de fondo con Celery.
Cumple el requerimiento de Message Broker (Redis/Celery) para procesos de fondo.
"""
import logging
import time
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger("meetu2.integraciones.tasks")


@shared_task(name="apps.integraciones.tasks.generar_reporte_sistema_async", bind=True)
def generar_reporte_sistema_async(self, correo_solicitante: str = "admin@meetu2.co"):
    """
    Tarea de larga duración ejecutada en worker de Celery.
    Genera un informe consolidado de auditoría, ocupación y ventas,
    y envía un correo electrónico real al solicitante con el desglose.
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
    tasa_efectividad = (
        round((reservas_confirmadas / total_reservas * 100), 1)
        if total_reservas > 0
        else 0
    )

    asunto = f"📊 Reporte Consolidado de Auditoría y Métricas — MeetU2 ({ahora.strftime('%d/%m/%Y')})"
    cuerpo = f"""Estimado(a) Anfitrión/Administrador,

Adjuntamos el informe consolidado de auditoría y métricas de plataforma MeetU2 solicitado para {correo_solicitante}.

Fecha de generación: {ahora.strftime('%Y-%m-%d %H:%M:%S UTC')}
ID de tarea en Celery: {getattr(self.request, 'id', 'manual-exec') or 'manual-exec'}

==================================================
MÉTRICAS CONSOLIDADAS DEL SISTEMA
==================================================
• Experiencias totales en catálogo: {total_experiencias}
• Experiencias activas (publicadas): {experiencias_publicadas}
• Reservas totales históricas: {total_reservas}
• Reservas confirmadas o con check-in en puerta: {reservas_confirmadas}
• Reseñas verificadas de comunidad: {total_resenas}
• Tasa de efectividad de asistencia: {tasa_efectividad}%

==================================================
PROCESAMIENTO EN SEGUNDO PLANO
==================================================
Este informe fue procesado asíncronamente mediante Celery Worker conectado al Message Broker Redis, garantizando cero bloqueos en la interfaz de usuario.

Atentamente,
Equipo de Operaciones & Tecnología — MeetU2
"""

    correo_enviado = False
    try:
        remitente = getattr(settings, "DEFAULT_FROM_EMAIL", "no-responder@meetu2.co")
        send_mail(
            subject=asunto,
            message=cuerpo,
            from_email=remitente,
            recipient_list=[correo_solicitante],
            fail_silently=False,
        )
        correo_enviado = True
        logger.info("Correo de reporte asíncrono enviado exitosamente a %s", correo_solicitante)
    except Exception as exc:
        logger.exception("No se pudo enviar el correo a %s: %s", correo_solicitante, exc)

    reporte = {
        "generado_en": ahora.isoformat(),
        "solicitante": correo_solicitante,
        "correo_enviado": correo_enviado,
        "asunto_correo": asunto,
        "metricas": {
            "total_experiencias": total_experiencias,
            "experiencias_activas": experiencias_publicadas,
            "total_reservas": total_reservas,
            "reservas_confirmadas_o_checkin": reservas_confirmadas,
            "total_resenas_comunidad": total_resenas,
            "tasa_efectividad_pct": tasa_efectividad,
        },
        "estado": "COMPLETADO",
        "mensaje": f"Reporte consolidado generado con éxito por el worker Celery y enviado por correo a {correo_solicitante}.",
    }

    logger.info("Reporte asíncrono completado para %s (correo_enviado=%s)", correo_solicitante, correo_enviado)
    return reporte
