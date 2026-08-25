"""
Contrato de notificacion.

Es un modulo de soporte (no un contexto de negocio): no tiene entidades ni
persistencia, solo un puerto y varias implementaciones intercambiables que la
Factory resuelve en tiempo de ejecucion.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Notificacion:
    destinatario: str
    asunto: str
    mensaje: str
    # Datos estructurados para canales que los aprovechan (push, plantillas).
    datos: dict[str, Any] = field(default_factory=dict)


class NotificadorPort(ABC):
    """Todo canal de salida cumple este contrato y solo este."""

    #: Identificador del canal, usado por la Factory como clave de registro.
    nombre: str = "abstracto"

    @abstractmethod
    def enviar(self, notificacion: Notificacion) -> bool:
        """Devuelve True si el envio se acepto. Nunca lanza por fallo de canal."""
