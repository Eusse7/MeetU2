"""
Persistencia propia del microservicio (database-per-service).

Pagos tiene su propia base de datos (`meetu2_pagos` en PostgreSQL, SQLite en
local/pruebas). No existe ninguna tabla compartida ni llave foranea hacia el
monolito: la reserva se referencia solo por su UUID.
"""
from abc import ABC, abstractmethod
from datetime import timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine

from pagos_service.domain import EstadoPago, MedioPago, Pago, ahora_utc

metadata = MetaData()

pagos = Table(
    "pagos_pago",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("id_reserva", String(36), nullable=False, index=True),
    Column("id_usuario", String(36), nullable=False, index=True),
    Column("id_organizador", String(36), nullable=False, index=True),
    Column("referencia", String(32), nullable=False, unique=True),
    Column("referencia_pasarela", String(64), nullable=False, default=""),
    Column("pasarela", String(20), nullable=False),
    Column("medio_pago", String(20), nullable=False),
    Column("moneda", String(3), nullable=False, default="COP"),
    Column("monto", Numeric(12, 2), nullable=False),
    Column("comision_plataforma", Numeric(12, 2), nullable=False),
    Column("monto_reembolsado", Numeric(12, 2), nullable=False, default=0),
    Column("estado", String(20), nullable=False, index=True),
    Column("motivo_rechazo", String(255), nullable=False, default=""),
    Column("reserva_confirmada", Boolean, nullable=False, default=False),
    Column("creado_en", DateTime(timezone=True), nullable=False),
    Column("actualizado_en", DateTime(timezone=True), nullable=False),
)


class PagoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, pago: Pago) -> Pago: ...

    @abstractmethod
    def obtener_por_id(self, id_pago: UUID) -> Pago | None: ...

    @abstractmethod
    def obtener_por_referencia(self, referencia: str) -> Pago | None: ...

    @abstractmethod
    def aprobado_de_reserva(self, id_reserva: UUID) -> Pago | None:
        """El pago vigente (APROBADO o reembolsado) de una reserva, si existe."""

    @abstractmethod
    def listar(self, id_reserva: UUID | None = None,
               id_usuario: UUID | None = None,
               id_organizador: UUID | None = None) -> list[Pago]: ...


class SqlPagoRepository(PagoRepositoryPort):
    def __init__(self, engine: Engine):
        self._engine = engine

    @classmethod
    def desde_url(cls, url: str) -> "SqlPagoRepository":
        engine = create_engine(url, future=True, pool_pre_ping=True)
        metadata.create_all(engine)
        # gunicorn --preload crea la app antes de hacer fork: se sueltan las
        # conexiones para que cada worker abra las suyas.
        engine.dispose()
        return cls(engine)

    def guardar(self, pago: Pago) -> Pago:
        pago.actualizado_en = ahora_utc()
        fila = self._a_fila(pago)
        with self._engine.begin() as cx:
            existe = cx.execute(
                select(pagos.c.id).where(pagos.c.id == fila["id"])
            ).first()
            if existe:
                cx.execute(update(pagos).where(pagos.c.id == fila["id"]).values(**fila))
            else:
                cx.execute(insert(pagos).values(**fila))
        return pago

    def obtener_por_id(self, id_pago: UUID) -> Pago | None:
        return self._uno(pagos.c.id == str(id_pago))

    def obtener_por_referencia(self, referencia: str) -> Pago | None:
        return self._uno(pagos.c.referencia == referencia)

    def aprobado_de_reserva(self, id_reserva: UUID) -> Pago | None:
        return self._uno(
            (pagos.c.id_reserva == str(id_reserva))
            & (pagos.c.estado != EstadoPago.RECHAZADO.value)
        )

    def listar(self, id_reserva=None, id_usuario=None, id_organizador=None):
        consulta = select(pagos).order_by(pagos.c.creado_en.desc())
        if id_reserva:
            consulta = consulta.where(pagos.c.id_reserva == str(id_reserva))
        if id_usuario:
            consulta = consulta.where(pagos.c.id_usuario == str(id_usuario))
        if id_organizador:
            consulta = consulta.where(pagos.c.id_organizador == str(id_organizador))
        with self._engine.connect() as cx:
            return [self._a_pago(f) for f in cx.execute(consulta).mappings()]

    def contar(self) -> int:
        with self._engine.connect() as cx:
            return cx.execute(select(func.count()).select_from(pagos)).scalar_one()

    # ----------------------------------------------------------- internos
    def _uno(self, condicion) -> Pago | None:
        with self._engine.connect() as cx:
            fila = cx.execute(select(pagos).where(condicion)).mappings().first()
        return self._a_pago(fila) if fila else None

    @staticmethod
    def _a_fila(pago: Pago) -> dict:
        return {
            "id": str(pago.id),
            "id_reserva": str(pago.id_reserva),
            "id_usuario": str(pago.id_usuario),
            "id_organizador": str(pago.id_organizador),
            "referencia": pago.referencia,
            "referencia_pasarela": pago.referencia_pasarela,
            "pasarela": pago.pasarela,
            "medio_pago": str(pago.medio_pago),
            "moneda": pago.moneda,
            "monto": pago.monto,
            "comision_plataforma": pago.comision_plataforma,
            "monto_reembolsado": pago.monto_reembolsado,
            "estado": str(pago.estado),
            "motivo_rechazo": pago.motivo_rechazo[:255],
            "reserva_confirmada": pago.reserva_confirmada,
            "creado_en": pago.creado_en,
            "actualizado_en": pago.actualizado_en,
        }

    @staticmethod
    def _a_pago(fila) -> Pago:
        return Pago(
            id=UUID(fila["id"]),
            id_reserva=UUID(fila["id_reserva"]),
            id_usuario=UUID(fila["id_usuario"]),
            id_organizador=UUID(fila["id_organizador"]),
            referencia=fila["referencia"],
            referencia_pasarela=fila["referencia_pasarela"],
            pasarela=fila["pasarela"],
            medio_pago=MedioPago(fila["medio_pago"]),
            moneda=fila["moneda"],
            monto=Decimal(fila["monto"]).quantize(Decimal("0.01")),
            comision_plataforma=Decimal(fila["comision_plataforma"]).quantize(Decimal("0.01")),
            monto_reembolsado=Decimal(fila["monto_reembolsado"]).quantize(Decimal("0.01")),
            estado=EstadoPago(fila["estado"]),
            motivo_rechazo=fila["motivo_rechazo"],
            reserva_confirmada=bool(fila["reserva_confirmada"]),
            creado_en=_con_zona(fila["creado_en"]),
            actualizado_en=_con_zona(fila["actualizado_en"]),
        )


def _con_zona(momento):
    """SQLite pierde la zona horaria al guardar; se asume UTC."""
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)
