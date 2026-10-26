"""Persistencia del microservicio Social con SQLAlchemy."""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, scoped_session

from social_service.domain import EstadoResena, ReputacionOrganizador, Resena

Base = declarative_base()


class ResenaORM(Base):
    __tablename__ = "social_resenas"

    id = Column(String(36), primary_key=True)
    reserva_id = Column(String(36), nullable=False, unique=True, index=True)
    usuario_id = Column(String(36), nullable=False, index=True)
    experiencia_id = Column(String(36), nullable=False, index=True)
    organizador_id = Column(String(36), nullable=False, index=True)
    calificacion = Column(Integer, nullable=False)
    comentario = Column(Text, default="", nullable=False)
    estado = Column(String(20), default=EstadoResena.PUBLICADA.value, nullable=False, index=True)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_domain(self) -> Resena:
        return Resena(
            id=uuid.UUID(self.id),
            reserva_id=uuid.UUID(self.reserva_id),
            usuario_id=uuid.UUID(self.usuario_id),
            experiencia_id=uuid.UUID(self.experiencia_id),
            organizador_id=uuid.UUID(self.organizador_id),
            calificacion=self.calificacion,
            comentario=self.comentario,
            estado=EstadoResena(self.estado),
            creado_en=self.creado_en,
        )

    @classmethod
    def from_domain(cls, resena: Resena) -> "ResenaORM":
        return cls(
            id=str(resena.id),
            reserva_id=str(resena.reserva_id),
            usuario_id=str(resena.usuario_id),
            experiencia_id=str(resena.experiencia_id),
            organizador_id=str(resena.organizador_id),
            calificacion=resena.calificacion,
            comentario=resena.comentario,
            estado=resena.estado.value,
            creado_en=resena.creado_en,
        )


class SQLAlchemyResenaRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def guardar(self, resena: Resena) -> Resena:
        session = self.session_factory()
        orm = session.query(ResenaORM).filter_by(id=str(resena.id)).first()
        if orm is None:
            orm = ResenaORM.from_domain(resena)
            session.add(orm)
        else:
            orm.calificacion = resena.calificacion
            orm.comentario = resena.comentario
            orm.estado = resena.estado.value
        session.commit()
        return orm.to_domain()

    def obtener_por_reserva(self, reserva_id: uuid.UUID) -> Optional[Resena]:
        session = self.session_factory()
        orm = session.query(ResenaORM).filter_by(reserva_id=str(reserva_id)).first()
        return orm.to_domain() if orm else None

    def obtener_por_id(self, resena_id: uuid.UUID) -> Optional[Resena]:
        session = self.session_factory()
        orm = session.query(ResenaORM).filter_by(id=str(resena_id)).first()
        return orm.to_domain() if orm else None

    def listar_por_experiencia(self, experiencia_id: uuid.UUID) -> List[Resena]:
        session = self.session_factory()
        orms = (
            session.query(ResenaORM)
            .filter_by(experiencia_id=str(experiencia_id), estado=EstadoResena.PUBLICADA.value)
            .order_by(ResenaORM.creado_en.desc())
            .all()
        )
        return [orm.to_domain() for orm in orms]

    def listar_por_organizador(self, organizador_id: uuid.UUID) -> List[Resena]:
        session = self.session_factory()
        orms = (
            session.query(ResenaORM)
            .filter_by(organizador_id=str(organizador_id), estado=EstadoResena.PUBLICADA.value)
            .order_by(ResenaORM.creado_en.desc())
            .all()
        )
        return [orm.to_domain() for orm in orms]

    def calcular_reputacion(self, organizador_id: uuid.UUID) -> ReputacionOrganizador:
        session = self.session_factory()
        query = (
            session.query(
                func.avg(ResenaORM.calificacion).label("promedio"),
                func.count(ResenaORM.id).label("total"),
            )
            .filter_by(organizador_id=str(organizador_id), estado=EstadoResena.PUBLICADA.value)
            .first()
        )
        promedio = float(query.promedio or 0.0) if query else 0.0
        total = int(query.total or 0) if query else 0
        return ReputacionOrganizador(
            organizador_id=organizador_id,
            promedio=round(promedio, 2),
            total_resenas=total,
        )
