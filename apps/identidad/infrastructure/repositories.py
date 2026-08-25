"""Adaptadores de persistencia del contexto Identidad."""
from uuid import UUID

from apps.identidad.application.ports import (
    InteresRepositoryPort,
    OrganizadorRepositoryPort,
    UsuarioRepositoryPort,
)
from apps.identidad.domain.models import InteresUsuario, Organizador, Usuario


class DjangoUsuarioRepository(UsuarioRepositoryPort):
    def guardar(self, usuario: Usuario) -> Usuario:
        usuario.full_clean(exclude=["id"])
        usuario.save()
        return usuario

    def obtener_por_id(self, id_usuario: UUID) -> Usuario | None:
        return Usuario.objects.filter(pk=id_usuario).first()

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        return Usuario.objects.filter(correo__iexact=correo).first()

    def existe_correo(self, correo: str) -> bool:
        return Usuario.objects.filter(correo__iexact=correo).exists()

    def listar(self) -> list[Usuario]:
        return list(Usuario.objects.all())


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
        return (
            Organizador.objects.select_related("usuario")
            .filter(usuario_id=id_usuario)
            .first()
        )


class DjangoInteresRepository(InteresRepositoryPort):
    def guardar(self, interes: InteresUsuario) -> InteresUsuario:
        interes.full_clean(exclude=["id"], validate_constraints=False)
        interes.save()
        return interes

    def listar_por_usuario(self, id_usuario: UUID) -> list[InteresUsuario]:
        return list(InteresUsuario.objects.filter(usuario_id=id_usuario))

    def obtener(self, id_usuario: UUID, id_categoria: UUID) -> InteresUsuario | None:
        return InteresUsuario.objects.filter(
            usuario_id=id_usuario, categoria_id=id_categoria
        ).first()

    def eliminar(self, id_usuario: UUID, id_categoria: UUID) -> bool:
        borrados, _ = InteresUsuario.objects.filter(
            usuario_id=id_usuario, categoria_id=id_categoria
        ).delete()
        return borrados > 0
