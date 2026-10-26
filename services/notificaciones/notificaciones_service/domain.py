"""Dominio puro del microservicio de Notificaciones."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid


class CanalNotificacion(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    ASINCRONO = "asincrono"


class EstadoNotificacion(str, Enum):
    ENVIADA = "ENVIADA"
    PENDIENTE = "PENDIENTE"
    FALLIDA = "FALLIDA"


@dataclass
class Notificacion:
    usuario_id: uuid.UUID
    canal: CanalNotificacion
    destinatario: str
    asunto: str
    mensaje: str
    estado: EstadoNotificacion = EstadoNotificacion.ENVIADA
    metadata_envio: str = "{}"
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.destinatario:
            raise ValueError("El destinatario es obligatorio")
        if not self.mensaje:
            raise ValueError("El mensaje de notificacion no puede estar vacio")
