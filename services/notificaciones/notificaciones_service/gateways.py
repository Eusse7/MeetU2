"""Pasarelas de despacho del microservicio de Notificaciones."""
import logging
from notificaciones_service.domain import CanalNotificacion

logger = logging.getLogger(__name__)


class NotificationSender:
    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> bool:
        raise NotImplementedError


class EmailSender(NotificationSender):
    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> bool:
        logger.info("[EMAIL] Enviando a %s | Asunto: %s", destinatario, asunto)
        return True


class SmsSender(NotificationSender):
    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> bool:
        logger.info("[SMS] Enviando a %s: %s", destinatario, mensaje[:50])
        return True


class PushSender(NotificationSender):
    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> bool:
        logger.info("[PUSH] Notificando token %s: %s", destinatario, asunto)
        return True


class SenderRegistry:
    def __init__(self):
        self._senders = {
            CanalNotificacion.EMAIL: EmailSender(),
            CanalNotificacion.SMS: SmsSender(),
            CanalNotificacion.PUSH: PushSender(),
            CanalNotificacion.ASINCRONO: EmailSender(),
        }

    def obtener_sender(self, canal: CanalNotificacion) -> NotificationSender:
        return self._senders.get(canal, EmailSender())
