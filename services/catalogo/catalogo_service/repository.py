"""Persistencia del microservicio de Catalogo con SQLAlchemy."""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

from catalogo_service.domain import Categoria, EstadoExperiencia, Experiencia, Modalidad, Ubicacion

Base = declarative_base()


class CategoriaORM(Base):
    __tablename__ = "catalogo_categorias"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    descripcion = Column(String(255), default="", nullable=False)
    activa = Column(Boolean, default=True, nullable=False)

    def to_domain(self) -> Categoria:
        return Categoria(
            id=uuid.UUID(self.id),
            nombre=self.nombre,
            slug=self.slug,
            descripcion=self.descripcion,
            activa=self.activa,
        )

    @classmethod
    def from_domain(cls, cat: Categoria) -> "CategoriaORM":
        return cls(
            id=str(cat.id),
            nombre=cat.nombre,
            slug=cat.slug,
            descripcion=cat.descripcion,
            activa=cat.activa,
        )


class UbicacionORM(Base):
    __tablename__ = "catalogo_ubicaciones"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(150), nullable=False)
    direccion = Column(String(255), nullable=False)
    ciudad = Column(String(100), nullable=False, index=True)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    aforo_maximo = Column(Integer, nullable=False)

    def to_domain(self) -> Ubicacion:
        return Ubicacion(
            id=uuid.UUID(self.id),
            nombre=self.nombre,
            direccion=self.direccion,
            ciudad=self.ciudad,
            latitud=self.latitud,
            longitud=self.longitud,
            aforo_maximo=self.aforo_maximo,
        )

    @classmethod
    def from_domain(cls, ubi: Ubicacion) -> "UbicacionORM":
        return cls(
            id=str(ubi.id),
            nombre=ubi.nombre,
            direccion=ubi.direccion,
            ciudad=ubi.ciudad,
            latitud=ubi.latitud,
            longitud=ubi.longitud,
            aforo_maximo=ubi.aforo_maximo,
        )


class ExperienciaORM(Base):
    __tablename__ = "catalogo_experiencias"

    id = Column(String(36), primary_key=True)
    organizador_id = Column(String(36), nullable=False, index=True)
    categoria_id = Column(String(36), nullable=False, index=True)
    ubicacion_id = Column(String(36), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    precio_cop = Column(Float, nullable=False)
    cupo_maximo = Column(Integer, nullable=False)
    cupos_disponibles = Column(Integer, nullable=False)
    fecha_evento = Column(DateTime(timezone=True), nullable=False)
    modalidad = Column(String(20), default=Modalidad.PRESENCIAL.value, nullable=False)
    estado = Column(String(20), default=EstadoExperiencia.PUBLICADA.value, nullable=False, index=True)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_domain(self) -> Experiencia:
        return Experiencia(
            id=uuid.UUID(self.id),
            organizador_id=uuid.UUID(self.organizador_id),
            categoria_id=uuid.UUID(self.categoria_id),
            ubicacion_id=uuid.UUID(self.ubicacion_id),
            titulo=self.titulo,
            descripcion=self.descripcion,
            precio_cop=self.precio_cop,
            cupo_maximo=self.cupo_maximo,
            cupos_disponibles=self.cupos_disponibles,
            fecha_evento=self.fecha_evento,
            modalidad=Modalidad(self.modalidad),
            estado=EstadoExperiencia(self.estado),
            creado_en=self.creado_en,
        )

    @classmethod
    def from_domain(cls, exp: Experiencia) -> "ExperienciaORM":
        return cls(
            id=str(exp.id),
            organizador_id=str(exp.organizador_id),
            categoria_id=str(exp.categoria_id),
            ubicacion_id=str(exp.ubicacion_id),
            titulo=exp.titulo,
            descripcion=exp.descripcion,
            precio_cop=exp.precio_cop,
            cupo_maximo=exp.cupo_maximo,
            cupos_disponibles=exp.cupos_disponibles,
            fecha_evento=exp.fecha_evento,
            modalidad=exp.modalidad.value,
            estado=exp.estado.value,
            creado_en=exp.creado_en,
        )


class SQLAlchemyCatalogoRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def guardar_categoria(self, categoria: Categoria) -> Categoria:
        session = self.session_factory()
        orm = session.query(CategoriaORM).filter_by(id=str(categoria.id)).first()
        if orm is None:
            orm = CategoriaORM.from_domain(categoria)
            session.add(orm)
        else:
            orm.nombre = categoria.nombre
            orm.descripcion = categoria.descripcion
            orm.activa = categoria.activa
        session.commit()
        return orm.to_domain()

    def listar_categorias(self) -> List[Categoria]:
        session = self.session_factory()
        orms = session.query(CategoriaORM).filter_by(activa=True).order_by(CategoriaORM.nombre).all()
        return [orm.to_domain() for orm in orms]

    def guardar_ubicacion(self, ubicacion: Ubicacion) -> Ubicacion:
        session = self.session_factory()
        orm = session.query(UbicacionORM).filter_by(id=str(ubicacion.id)).first()
        if orm is None:
            orm = UbicacionORM.from_domain(ubicacion)
            session.add(orm)
        session.commit()
        return orm.to_domain()

    def obtener_ubicacion(self, ubicacion_id: uuid.UUID) -> Optional[Ubicacion]:
        session = self.session_factory()
        orm = session.query(UbicacionORM).filter_by(id=str(ubicacion_id)).first()
        return orm.to_domain() if orm else None

    def listar_ubicaciones(self) -> List[Ubicacion]:
        session = self.session_factory()
        orms = session.query(UbicacionORM).order_by(UbicacionORM.ciudad, UbicacionORM.nombre).all()
        return [orm.to_domain() for orm in orms]

    def guardar_experiencia(self, exp: Experiencia) -> Experiencia:
        session = self.session_factory()
        orm = session.query(ExperienciaORM).filter_by(id=str(exp.id)).first()
        if orm is None:
            orm = ExperienciaORM.from_domain(exp)
            session.add(orm)
        else:
            orm.titulo = exp.titulo
            orm.descripcion = exp.descripcion
            orm.precio_cop = exp.precio_cop
            orm.cupos_disponibles = exp.cupos_disponibles
            orm.estado = exp.estado.value
        session.commit()
        return orm.to_domain()

    def obtener_experiencia(self, exp_id: uuid.UUID) -> Optional[Experiencia]:
        session = self.session_factory()
        orm = session.query(ExperienciaORM).filter_by(id=str(exp_id)).first()
        return orm.to_domain() if orm else None

    def listar_experiencias(
        self,
        categoria_id: Optional[uuid.UUID] = None,
        precio_max: Optional[float] = None,
    ) -> List[Experiencia]:
        session = self.session_factory()
        query = session.query(ExperienciaORM).filter_by(estado=EstadoExperiencia.PUBLICADA.value)
        if categoria_id:
            query = query.filter_by(categoria_id=str(categoria_id))
        if precio_max is not None:
            query = query.filter(ExperienciaORM.precio_cop <= precio_max)
        orms = query.order_by(ExperienciaORM.creado_en.desc()).all()
        return [orm.to_domain() for orm in orms]
