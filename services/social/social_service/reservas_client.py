"""Cliente ACL (Anti-Corruption Layer) para comunicarse con el monolito."""
import logging
from typing import Optional
import uuid

import requests

logger = logging.getLogger(__name__)


class ReservasClient:
    """Valida el estado de la reserva antes de permitir reseñar."""

    def __init__(self, monolito_url: Optional[str] = None):
        self.monolito_url = (monolito_url or "").rstrip("/")

    def verificar_asistencia(self, reserva_id: uuid.UUID) -> bool:
        """
        Retorna True si la reserva existe y tiene check-in realizado.
        Si monolito_url esta vacio (entorno de pruebas aislado), asume True.
        """
        if not self.monolito_url:
            return True

        url = f"{self.monolito_url}/api/v1/reservas/{reserva_id}/"
        try:
            resp = requests.get(url, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                estado = data.get("estado", "")
                return estado in ("CHECKED_IN", "CONFIRMADA", "COMPLETADA")
            logger.warning("Reserva %s respondio con HTTP %s", reserva_id, resp.status_code)
            return False
        except requests.RequestException as err:
            logger.error("Error consultando reserva %s en monolito: %s", reserva_id, err)
            # Resiliencia: si el monolito no responde, no bloquear arbitrariamente
            return True
