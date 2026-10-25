"""
Tareas asíncronas de notificación mediante Celery y Redis.
Procesamiento en segundo plano de correos y alertas (Entregable 2).
"""
import logging
from celery import shared_task

from apps.notificaciones.application.ports import Notificacion

logger = logging.getLogger("meetu2.notificaciones.async")


@shared_task(name="apps.notificaciones.tasks.enviar_notificacion_asincrona")
def enviar_notificacion_asincrona(
    destinatario: str,
    asunto: str,
    mensaje: str,
    canal: str = "consola",
    datos: dict | None = None,
) -> bool:
    """Ejecuta el envío de la notificación en el worker de Celery."""
    from apps.notificaciones.infrastructure.factories import NotificadorFactory

    logger.info("Procesando notificación asíncrona para %s (canal=%s)", destinatario, canal)
    try:
        notificador = NotificadorFactory.crear(canal)
        notif = Notificacion(
            destinatario=destinatario,
            asunto=asunto,
            mensaje=mensaje,
            datos=datos or {},
        )
        exito = notificador.enviar(notif)
        return exito
    except Exception as exc:
        logger.error("Error al enviar notificación asíncrona: %s", exc)
        return False
