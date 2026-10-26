"""Persistencia del microservicio de Notificaciones con SQLAlchemy."""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import declarative_base

from notificaciones_service.domain import CanalNotificacion, EstadoNotificacion, Notificacion

Base = declarative_base()


class NotificacionORM(Base):
    __tablename__ = "notificaciones_log"

    id = Column(String(36), primary_key=True)
    usuario_id = Column(String(36), nullable=False, index=True)
    canal = Column(String(20), nullable=False, index=True)
    destinatario = Column(String(255), nullable=False)
    asunto = Column(String(255), nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(20), default=EstadoNotificacion.ENVIADA.value, nullable=False, index=True)
    metadata_envio = Column(Text, default="{}", nullable=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_domain(self) -> Notificacion:
        return Notificacion(
            id=uuid.UUID(self.id),
            usuario_id=uuid.UUID(self.usuario_id),
            canal=CanalNotificacion(self.canal),
            destinatario=self.destinatario,
            asunto=self.asunto,
            mensaje=self.mensaje,
            estado=EstadoNotificacion(self.estado),
            metadata_envio=self.metadata_envio,
            creado_en=self.creado_en,
        )

    @classmethod
    def from_domain(cls, notif: Notificacion) -> "NotificacionORM":
        return cls(
            id=str(notif.id),
            usuario_id=str(notif.usuario_id),
            canal=notif.canal.value,
            destinatario=notif.destinatario,
            asunto=notif.asunto,
            mensaje=notif.mensaje,
            estado=notif.estado.value,
            metadata_envio=notif.metadata_envio,
            creado_en=notif.creado_en,
        )


class SQLAlchemyNotificacionRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def guardar(self, notificacion: Notificacion) -> Notificacion:
        session = self.session_factory()
        orm = session.query(NotificacionORM).filter_by(id=str(notificacion.id)).first()
        if orm is None:
            orm = NotificacionORM.from_domain(notificacion)
            session.add(orm)
        else:
            orm.estado = notificacion.estado.value
            orm.metadata_envio = notificacion.metadata_envio
        session.commit()
        return orm.to_domain()

    def obtener_por_id(self, notificacion_id: uuid.UUID) -> Optional[Notificacion]:
        session = self.session_factory()
        orm = session.query(NotificacionORM).filter_by(id=str(notificacion_id)).first()
        return orm.to_domain() if orm else None

    def listar_por_usuario(self, usuario_id: uuid.UUID) -> List[Notificacion]:
        session = self.session_factory()
        orms = (
            session.query(NotificacionORM)
            .filter_by(usuario_id=str(usuario_id))
            .order_by(NotificacionORM.creado_en.desc())
            .all()
        )
        return [orm.to_domain() for orm in orms]
