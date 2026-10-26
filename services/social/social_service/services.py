"""Casos de uso del microservicio Social."""
from typing import List, Optional
import uuid

from social_service.domain import EstadoResena, ReputacionOrganizador, Resena
from social_service.errors import (
    CalificacionInvalidaError,
    ResenaNoEncontradaError,
    ResenaYaExisteError,
    ReservaNoAptaError,
)
from social_service.repository import SQLAlchemyResenaRepository
from social_service.reservas_client import ReservasClient


class SocialService:
    def __init__(self, repository: SQLAlchemyResenaRepository, reservas_client: ReservasClient):
        self.repository = repository
        self.reservas_client = reservas_client

    def crear_resena(
        self,
        reserva_id: uuid.UUID,
        usuario_id: uuid.UUID,
        experiencia_id: uuid.UUID,
        organizador_id: uuid.UUID,
        calificacion: int,
        comentario: str = "",
        verificar_checkin: bool = True,
    ) -> Resena:
        if not (1 <= calificacion <= 5):
            raise CalificacionInvalidaError(calificacion)

        existente = self.repository.obtener_por_reserva(reserva_id)
        if existente:
            raise ResenaYaExisteError(str(reserva_id))

        if verificar_checkin:
            apta = self.reservas_client.verificar_asistencia(reserva_id)
            if not apta:
                raise ReservaNoAptaError(
                    f"La reserva {reserva_id} no cuenta con check-in o asistencia confirmada."
                )

        resena = Resena(
            reserva_id=reserva_id,
            usuario_id=usuario_id,
            experiencia_id=experiencia_id,
            organizador_id=organizador_id,
            calificacion=calificacion,
            comentario=comentario.strip(),
            estado=EstadoResena.PUBLICADA,
        )
        return self.repository.guardar(resena)

    def listar_resenas_experiencia(self, experiencia_id: uuid.UUID) -> List[Resena]:
        return self.repository.listar_por_experiencia(experiencia_id)

    def listar_resenas_organizador(self, organizador_id: uuid.UUID) -> List[Resena]:
        return self.repository.listar_por_organizador(organizador_id)

    def obtener_reputacion_organizador(self, organizador_id: uuid.UUID) -> ReputacionOrganizador:
        return self.repository.calcular_reputacion(organizador_id)

    def moderar_resena(self, resena_id: uuid.UUID, nuevo_estado: EstadoResena) -> Resena:
        resena = self.repository.obtener_por_id(resena_id)
        if not resena:
            raise ResenaNoEncontradaError(str(resena_id))
        resena.estado = nuevo_estado
        return self.repository.guardar(resena)
