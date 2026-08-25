"""Canal de desarrollo: escribe en el log. Es el valor por defecto."""
import logging

from apps.notificaciones.application.ports import Notificacion, NotificadorPort

logger = logging.getLogger("meetu2.notificaciones")


class NotificadorConsola(NotificadorPort):
    nombre = "consola"

    def enviar(self, notificacion: Notificacion) -> bool:
        logger.info(
            "[NOTIFICACION] para=%s | %s | %s",
            notificacion.destinatario,
            notificacion.asunto,
            notificacion.mensaje,
        )
        print(
            f"\n--- NOTIFICACION ({self.nombre}) ---\n"
            f"Para   : {notificacion.destinatario}\n"
            f"Asunto : {notificacion.asunto}\n"
            f"{notificacion.mensaje}\n"
            f"---------------------------------\n"
        )
        return True
