"""Canal de correo. Usa el backend de Django configurado en settings."""
import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.notificaciones.application.ports import Notificacion, NotificadorPort

logger = logging.getLogger("meetu2.notificaciones")


class NotificadorEmail(NotificadorPort):
    nombre = "email"

    def enviar(self, notificacion: Notificacion) -> bool:
        try:
            send_mail(
                subject=notificacion.asunto,
                message=notificacion.mensaje,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[notificacion.destinatario],
                fail_silently=False,
            )
            return True
        except Exception:
            # Un fallo de canal no puede tumbar una reserva ya confirmada.
            logger.exception(
                "No se pudo enviar el correo a %s", notificacion.destinatario
            )
            return False
