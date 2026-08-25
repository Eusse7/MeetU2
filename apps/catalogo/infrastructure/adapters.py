"""
Capa anticorrupcion hacia el contexto Identidad.

Catalogo nunca importa entidades de Identidad en su capa de aplicacion: habla
con los puertos `OrganizadorPort` e `InteresesUsuarioPort`. Estos adaptadores
son la unica costura entre ambos modulos.

Hoy resuelven la consulta en proceso (monolito modular). El dia que Identidad
se extraiga a un servicio propio basta con reemplazar el cuerpo de estos
metodos por una llamada HTTP: ni un servicio ni un test cambian.
"""
from uuid import UUID

from apps.catalogo.application.ports import InteresesUsuarioPort, OrganizadorPort
from apps.identidad.domain.models import InteresUsuario, Organizador
from apps.shared.domain.enums import EstadoValidacion


class IdentidadOrganizadorAdapter(OrganizadorPort):
    def existe(self, id_organizador: UUID) -> bool:
        return Organizador.objects.filter(pk=id_organizador).exists()

    def esta_verificado(self, id_organizador: UUID) -> bool:
        return Organizador.objects.filter(
            pk=id_organizador, estado_verificacion=EstadoValidacion.VERIFICADO
        ).exists()

    def nombre_comercial(self, id_organizador: UUID) -> str:
        return (
            Organizador.objects.filter(pk=id_organizador)
            .values_list("nombre_comercial", flat=True)
            .first()
            or ""
        )


class IdentidadInteresesAdapter(InteresesUsuarioPort):
    def obtener(self, id_usuario: UUID) -> dict[str, int]:
        filas = InteresUsuario.objects.filter(usuario_id=id_usuario).values_list(
            "categoria_id", "nivel_afinidad"
        )
        return {str(categoria_id): nivel for categoria_id, nivel in filas}
