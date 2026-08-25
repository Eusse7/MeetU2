from uuid import UUID

from apps.identidad.application.ports import (
    OrganizadorRepositoryPort,
    UsuarioRepositoryPort,
)
from apps.identidad.domain.models import Organizador, Usuario


class DjangoUsuarioRepository(UsuarioRepositoryPort):
    def guardar(self, usuario: Usuario) -> Usuario:
        usuario.full_clean(exclude=["id"])
        usuario.save()
        return usuario

    def obtener_por_id(self, id_usuario: UUID) -> Usuario | None:
        return Usuario.objects.filter(pk=id_usuario).first()

    def existe_correo(self, correo: str) -> bool:
        return Usuario.objects.filter(correo__iexact=correo).exists()


class DjangoOrganizadorRepository(OrganizadorRepositoryPort):
    def guardar(self, organizador: Organizador) -> Organizador:
        organizador.full_clean(exclude=["id"])
        organizador.save()
        return organizador

    def obtener_por_id(self, id_organizador: UUID) -> Organizador | None:
        return (
            Organizador.objects.select_related("usuario")
            .filter(pk=id_organizador)
            .first()
        )

    def obtener_por_usuario(self, id_usuario: UUID) -> Organizador | None:
        return Organizador.objects.filter(usuario_id=id_usuario).first()