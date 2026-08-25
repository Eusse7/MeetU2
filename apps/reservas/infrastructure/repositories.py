"""Adaptador de persistencia del contexto Reservas."""
from uuid import UUID

from apps.reservas.application.ports import ReservaRepositoryPort
from apps.reservas.domain.models import Reserva
from apps.reservas.domain.policies import MaquinaEstadosReserva


class DjangoReservaRepository(ReservaRepositoryPort):
    def guardar(self, reserva: Reserva) -> Reserva:
        reserva.full_clean(exclude=["id"], validate_constraints=False)
        reserva.save()
        return reserva

    def obtener_por_id(self, id_reserva: UUID) -> Reserva | None:
        return Reserva.objects.filter(pk=id_reserva).first()

    def obtener_por_ticket(self, codigo_ticket: str) -> Reserva | None:
        return Reserva.objects.filter(codigo_ticket=codigo_ticket).first()

    def listar_por_usuario(self, id_usuario: UUID) -> list[Reserva]:
        return list(Reserva.objects.filter(usuario_id=id_usuario))

    def listar_por_experiencia(self, id_experiencia: UUID) -> list[Reserva]:
        return list(Reserva.objects.filter(experiencia_id=id_experiencia))

    def existe_activa(self, id_usuario: UUID, id_experiencia: UUID) -> bool:
        # "Activa" = el estado sigue reteniendo cupo. La definicion es del
        # dominio; el repositorio solo la traduce a una consulta.
        return Reserva.objects.filter(
            usuario_id=id_usuario,
            experiencia_id=id_experiencia,
            estado__in=list(MaquinaEstadosReserva.ESTADOS_QUE_RETIENEN_CUPO),
        ).exists()

    def existe_ticket(self, codigo_ticket: str) -> bool:
        return Reserva.objects.filter(codigo_ticket=codigo_ticket).exists()

    def listar_pendientes_vencidas(self, ahora) -> list[Reserva]:
        """Consulta de apoyo para el job de expiracion."""
        from apps.reservas.domain.enums import EstadoReserva

        return list(
            Reserva.objects.filter(
                estado=EstadoReserva.PENDIENTE_PAGO, vence_en__lt=ahora
            )
        )
