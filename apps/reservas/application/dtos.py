"""Objetos de transferencia del contexto Reservas."""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class SolicitarReservaDTO:
    id_usuario: UUID
    id_experiencia: UUID
    cantidad_cupos: int = 1


@dataclass(frozen=True)
class ConfirmarReservaDTO:
    id_reserva: UUID
    referencia_pago: str = ""


@dataclass(frozen=True)
class CancelarReservaDTO:
    id_reserva: UUID
    id_usuario: UUID
    motivo: str = ""


@dataclass(frozen=True)
class CheckInDTO:
    codigo_ticket: str
    id_organizador: UUID


@dataclass(frozen=True)
class ResultadoCancelacionDTO:
    reserva: object
    monto_reembolsado: Decimal
    porcentaje_aplicado: Decimal


@dataclass(frozen=True)
class ReservaDetalladaDTO:
    """Reserva compuesta con datos de la experiencia (vista para el usuario)."""

    reserva: object
    experiencia_titulo: str
    experiencia_fecha: object
    experiencia_ciudad: str
