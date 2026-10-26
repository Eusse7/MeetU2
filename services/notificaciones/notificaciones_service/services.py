"""Servicio de aplicacion del microservicio Notificaciones."""
import json
from typing import Any, Dict, List, Optional
import uuid

from notificaciones_service.domain import CanalNotificacion, EstadoNotificacion, Notificacion
from notificaciones_service.gateways import SenderRegistry
from notificaciones_service.repository import SQLAlchemyNotificacionRepository


class NotificacionesService:
    def __init__(self, repository: SQLAlchemyNotificacionRepository, sender_registry: SenderRegistry):
        self.repository = repository
        self.sender_registry = sender_registry

    def despachar(
        self,
        usuario_id: uuid.UUID,
        canal: CanalNotificacion,
        destinatario: str,
        asunto: str,
        mensaje: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notificacion:
        sender = self.sender_registry.obtener_sender(canal)
        try:
            exito = sender.enviar(destinatario=destinatario, asunto=asunto, mensaje=mensaje)
            estado = EstadoNotificacion.ENVIADA if exito else EstadoNotificacion.FALLIDA
        except Exception:
            estado = EstadoNotificacion.FALLIDA

        notif = Notificacion(
            usuario_id=usuario_id,
            canal=canal,
            destinatario=destinatario,
            asunto=asunto,
            mensaje=mensaje,
            estado=estado,
            metadata_envio=json.dumps(metadata or {}),
        )
        return self.repository.guardar(notif)

    def consultar_historial(self, usuario_id: uuid.UUID) -> List[Notificacion]:
        return self.repository.listar_por_usuario(usuario_id)
