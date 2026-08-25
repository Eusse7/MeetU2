"""
Canal push. Placeholder del proveedor real (FCM / APNs).

Existe para demostrar que agregar un canal nuevo no obliga a tocar ni un solo
servicio de la capa de aplicacion: basta con implementar el puerto y
registrarlo en la Factory (principio Abierto/Cerrado).
"""
import logging

from apps.notificaciones.application.ports import Notificacion, NotificadorPort

logger = logging.getLogger("meetu2.notificaciones")


class NotificadorPush(NotificadorPort):
    nombre = "push"

    def enviar(self, notificacion: Notificacion) -> bool:
        logger.info(
            "[PUSH simulado] token=%s titulo=%s datos=%s",
            notificacion.destinatario,
            notificacion.asunto,
            notificacion.datos,
        )
        return True
