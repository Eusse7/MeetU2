"""Adaptadores de persistencia del contexto Social."""
from uuid import UUID

from apps.social.application.ports import ResenaRepositoryPort
from apps.social.domain.enums import EstadoResena
from apps.social.domain.models import Resena


class DjangoResenaRepository(ResenaRepositoryPort):
    def guardar(self, resena: Resena) -> Resena:
        resena.full_clean(exclude=["id"], validate_constraints=False)
        resena.save()
        return resena

    def obtener_por_id(self, id_resena: UUID) -> Resena | None:
        return Resena.objects.filter(pk=id_resena).first()

    def obtener_por_reserva(self, id_reserva: UUID) -> Resena | None:
        return Resena.objects.filter(reserva_id=id_reserva).first()

    def listar_por_experiencia(self, id_experiencia: UUID) -> list[Resena]:
        return list(
            Resena.objects.filter(
                experiencia_id=id_experiencia, estado=EstadoResena.PUBLICADA
            ).order_by("-creado_en")
        )

    def listar_por_organizador(self, id_organizador: UUID) -> list[Resena]:
        return list(
            Resena.objects.filter(
                organizador_id=id_organizador, estado=EstadoResena.PUBLICADA
            ).order_by("-creado_en")
        )

    def listar_por_usuario(self, id_usuario: UUID) -> list[Resena]:
        return list(
            Resena.objects.filter(usuario_id=id_usuario).order_by("-creado_en")
        )

    def listar_recientes(self, limite: int = 20) -> list[Resena]:
        return list(
            Resena.objects.filter(estado=EstadoResena.PUBLICADA).order_by("-creado_en")[:limite]
        )

    def obtener_calificaciones_organizador(self, id_organizador: UUID) -> list[int]:
        return list(
            Resena.objects.filter(
                organizador_id=id_organizador, estado=EstadoResena.PUBLICADA
            ).values_list("calificacion", flat=True)
        )

    def obtener_calificaciones_experiencia(self, id_experiencia: UUID) -> list[int]:
        return list(
            Resena.objects.filter(
                experiencia_id=id_experiencia, estado=EstadoResena.PUBLICADA
            ).values_list("calificacion", flat=True)
        )
