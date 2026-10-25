"""Dobles de prueba para el contexto Social."""
from decimal import Decimal
from uuid import UUID, uuid4

from apps.social.application.ports import (
    OrganizadorCalificacionPort,
    ResenaRepositoryPort,
    ReservaAsistenciaPort,
    ReservaAsistenciaVista,
)
from apps.social.domain.enums import EstadoResena
from apps.social.domain.models import Resena


class ResenaRepositoryEnMemoria(ResenaRepositoryPort):
    def __init__(self, resenas: list[Resena] | None = None):
        self.items = list(resenas or [])

    def guardar(self, resena: Resena) -> Resena:
        if resena.id is None:
            resena.id = uuid4()
        if resena not in self.items:
            self.items.append(resena)
        return resena

    def obtener_por_id(self, id_resena: UUID) -> Resena | None:
        return next((r for r in self.items if r.id == id_resena), None)

    def obtener_por_reserva(self, id_reserva: UUID) -> Resena | None:
        return next((r for r in self.items if r.reserva_id == id_reserva), None)

    def listar_por_experiencia(self, id_experiencia: UUID) -> list[Resena]:
        return [
            r
            for r in self.items
            if r.experiencia_id == id_experiencia and r.estado == EstadoResena.PUBLICADA
        ]

    def listar_por_organizador(self, id_organizador: UUID) -> list[Resena]:
        return [
            r
            for r in self.items
            if r.organizador_id == id_organizador and r.estado == EstadoResena.PUBLICADA
        ]

    def listar_por_usuario(self, id_usuario: UUID) -> list[Resena]:
        return [r for r in self.items if r.usuario_id == id_usuario]

    def listar_recientes(self, limite: int = 20) -> list[Resena]:
        return [r for r in self.items if r.estado == EstadoResena.PUBLICADA][:limite]

    def obtener_calificaciones_organizador(self, id_organizador: UUID) -> list[int]:
        return [
            r.calificacion
            for r in self.items
            if r.organizador_id == id_organizador and r.estado == EstadoResena.PUBLICADA
        ]

    def obtener_calificaciones_experiencia(self, id_experiencia: UUID) -> list[int]:
        return [
            r.calificacion
            for r in self.items
            if r.experiencia_id == id_experiencia and r.estado == EstadoResena.PUBLICADA
        ]


class ReservaAsistenciaFalsa(ReservaAsistenciaPort):
    def __init__(self, reservas: list[ReservaAsistenciaVista] | None = None):
        self.reservas = {r.id: r for r in (reservas or [])}

    def registrar(self, reserva: ReservaAsistenciaVista) -> None:
        self.reservas[reserva.id] = reserva

    def obtener_asistencia(self, id_reserva: UUID) -> ReservaAsistenciaVista | None:
        return self.reservas.get(id_reserva)


class OrganizadorCalificacionEspia(OrganizadorCalificacionPort):
    def __init__(self):
        self.promedios: dict[UUID, Decimal] = {}

    def actualizar_calificacion_promedio(
        self, id_organizador: UUID, calificacion_promedio: Decimal
    ) -> None:
        self.promedios[id_organizador] = calificacion_promedio
