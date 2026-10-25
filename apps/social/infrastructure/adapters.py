"""
Adaptadores de infraestructura del contexto Social hacia Reservas e Identidad.

Resuelven los puertos definidos en la capa de aplicacion (`ReservaAsistenciaPort`,
`OrganizadorCalificacionPort`) conectando con los modelos correspondientes en
proceso (monolito modular). Si cualquiera de los modulos se extrae a un
microservicio independiente, solo se modifica esta capa.
"""
from decimal import Decimal
from uuid import UUID

from apps.identidad.domain.models import Organizador
from apps.reservas.domain.models import Reserva
from apps.social.application.ports import (
    OrganizadorCalificacionPort,
    ReservaAsistenciaPort,
    ReservaAsistenciaVista,
)


class ReservaAsistenciaAdapter(ReservaAsistenciaPort):
    """Consulta la reserva en el contexto Reservas para validar asistencia."""

    def obtener_asistencia(self, id_reserva: UUID) -> ReservaAsistenciaVista | None:
        reserva = Reserva.objects.filter(pk=id_reserva).first()
        if reserva is None:
            return None
        return ReservaAsistenciaVista(
            id=reserva.id,
            usuario_id=reserva.usuario_id,
            experiencia_id=reserva.experiencia_id,
            organizador_id=reserva.organizador_id,
            estado=reserva.estado,
            check_in_en=reserva.check_in_en,
        )


class IdentidadOrganizadorCalificacionAdapter(OrganizadorCalificacionPort):
    """Actualiza la calificacion promedio del organizador en el contexto Identidad."""

    def actualizar_calificacion_promedio(
        self, id_organizador: UUID, calificacion_promedio: Decimal
    ) -> None:
        Organizador.objects.filter(pk=id_organizador).update(
            calificacion_promedio=calificacion_promedio
        )
