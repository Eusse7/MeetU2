"""
Patron Factory: `NotificadorFactory`.

Por que Factory aqui:

1. La eleccion del canal es una **decision de configuracion, no de codigo**. En
   desarrollo se escribe en consola, en produccion se manda correo o push. El
   servicio que confirma una reserva no debe enterarse de ese cambio.
2. Concentra la construccion en un unico punto: si manana el canal de correo
   necesita credenciales o un cliente HTTP, se arma aqui y nadie mas cambia.
3. Es extensible sin modificar lo existente (Abierto/Cerrado): un canal nuevo
   se registra con `NotificadorFactory.registrar(...)`.

    >>> NotificadorFactory.crear()          # lee CANAL_NOTIFICACION de settings
    >>> NotificadorFactory.crear("email")   # forzado explicito
"""
from django.conf import settings

from apps.notificaciones.application.ports import NotificadorPort
from apps.notificaciones.infrastructure.canales.consola import NotificadorConsola
from apps.notificaciones.infrastructure.canales.email import NotificadorEmail
from apps.notificaciones.infrastructure.canales.push import NotificadorPush


class CanalNoSoportado(ValueError):
    """Error de configuracion, no de negocio: debe fallar ruidosamente."""


class NotificadorFactory:
    """Fabrica de canales de notificacion registrados por nombre."""

    _registro: dict[str, type[NotificadorPort]] = {
        NotificadorConsola.nombre: NotificadorConsola,
        NotificadorEmail.nombre: NotificadorEmail,
        NotificadorPush.nombre: NotificadorPush,
    }

    @classmethod
    def registrar(cls, clase: type[NotificadorPort]) -> None:
        """Da de alta un canal nuevo sin modificar esta clase."""
        cls._registro[clase.nombre] = clase

    @classmethod
    def canales_disponibles(cls) -> list[str]:
        return sorted(cls._registro)

    @classmethod
    def crear(cls, canal: str | None = None) -> NotificadorPort:
        nombre = (canal or getattr(settings, "CANAL_NOTIFICACION_DEFECTO", "consola")).lower()
        try:
            return cls._registro[nombre]()
        except KeyError:
            raise CanalNoSoportado(
                f"Canal de notificacion desconocido: {nombre!r}. "
                f"Disponibles: {', '.join(cls.canales_disponibles())}"
            ) from None
