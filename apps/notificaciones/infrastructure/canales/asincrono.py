"""
Canal asíncrono que encola notificaciones en el Message Broker (Redis/Celery).
Cumple con los requerimientos de procesamiento en segundo plano del Entregable 2.
"""
import logging
from apps.notificaciones.application.ports import Notificacion, NotificadorPort

logger = logging.getLogger("meetu2.notificaciones.celery")


class NotificadorCelery(NotificadorPort):
    nombre = "asincrono"

    def __init__(self, canal_destino: str = "consola"):
        self._canal_destino = canal_destino

    def enviar(self, notificacion: Notificacion) -> bool:
        from apps.notificaciones.tasks import enviar_notificacion_asincrona

        try:
            # Encola la tarea en el broker Redis
            enviar_notificacion_asincrona.delay(
                destinatario=notificacion.destinatario,
                asunto=notificacion.asunto,
                mensaje=notificacion.mensaje,
                canal=self._canal_destino,
                datos=notificacion.datos,
            )
            logger.info("Notificación para %s encolada en Celery", notificacion.destinatario)
            return True
        except Exception as exc:
            logger.warning("Fallo al encolar en Celery (%s). Enviando sincrónico como respaldo.", exc)
            # En caso de que Celery/Redis no esté disponible, ejecuta en consola
            from apps.notificaciones.infrastructure.canales.consola import NotificadorConsola
            return NotificadorConsola().enviar(notificacion)
