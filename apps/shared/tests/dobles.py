"""
Dobles de prueba compartidos.

Que estos repositorios en memoria sean suficientes para ejercitar los casos de
uso completos es la demostracion practica del desacoplamiento: ningun servicio
sabe que detras habia Django.
"""
from uuid import UUID, uuid4

from apps.identidad.application.ports import (
    CatalogoCategoriasPort,
    InteresRepositoryPort,
    OrganizadorRepositoryPort,
    UsuarioRepositoryPort,
)
from apps.reservas.application.ports import (
    CatalogoPort,
    NotificadorPort,
    PerfilUsuarioPort,
    ReservaRepositoryPort,
)


# --------------------------------------------------------------- Identidad
class UsuarioRepositoryEnMemoria(UsuarioRepositoryPort):
    def __init__(self, usuarios=()):
        self.items = {u.id: u for u in usuarios}

    def guardar(self, usuario):
        if usuario.id is None:
            usuario.id = uuid4()
        self.items[usuario.id] = usuario
        return usuario

    def obtener_por_id(self, id_usuario):
        return self.items.get(id_usuario)

    def obtener_por_correo(self, correo):
        return next(
            (u for u in self.items.values() if u.correo.lower() == correo.lower()),
            None,
        )

    def existe_correo(self, correo):
        return self.obtener_por_correo(correo) is not None

    def listar(self):
        return list(self.items.values())


class OrganizadorRepositoryEnMemoria(OrganizadorRepositoryPort):
    def __init__(self, organizadores=()):
        self.items = {o.id: o for o in organizadores}

    def guardar(self, organizador):
        if organizador.id is None:
            organizador.id = uuid4()
        self.items[organizador.id] = organizador
        return organizador

    def obtener_por_id(self, id_organizador):
        return self.items.get(id_organizador)

    def obtener_por_usuario(self, id_usuario):
        return next(
            (o for o in self.items.values() if o.usuario_id == id_usuario), None
        )


class InteresRepositoryEnMemoria(InteresRepositoryPort):
    def __init__(self):
        self.items: list = []

    def guardar(self, interes):
        if interes not in self.items:
            self.items.append(interes)
        return interes

    def listar_por_usuario(self, id_usuario):
        return [i for i in self.items if i.usuario_id == id_usuario]

    def obtener(self, id_usuario, id_categoria):
        return next(
            (
                i
                for i in self.items
                if i.usuario_id == id_usuario and i.categoria_id == id_categoria
            ),
            None,
        )

    def eliminar(self, id_usuario, id_categoria):
        interes = self.obtener(id_usuario, id_categoria)
        if interes is None:
            return False
        self.items.remove(interes)
        return True


class CategoriasSiempreExisten(CatalogoCategoriasPort):
    def __init__(self, existentes: set[UUID] | None = None):
        self.existentes = existentes

    def existe_categoria(self, id_categoria):
        return self.existentes is None or id_categoria in self.existentes


# ---------------------------------------------------------------- Reservas
class ReservaRepositoryEnMemoria(ReservaRepositoryPort):
    def __init__(self, reservas=()):
        self.items = list(reservas)

    def guardar(self, reserva):
        if reserva.id is None:
            reserva.id = uuid4()
        if reserva not in self.items:
            self.items.append(reserva)
        return reserva

    def obtener_por_id(self, id_reserva):
        return next((r for r in self.items if r.id == id_reserva), None)

    def obtener_por_ticket(self, codigo_ticket):
        return next((r for r in self.items if r.codigo_ticket == codigo_ticket), None)

    def listar_por_usuario(self, id_usuario):
        return [r for r in self.items if r.usuario_id == id_usuario]

    def listar_por_experiencia(self, id_experiencia):
        return [r for r in self.items if r.experiencia_id == id_experiencia]

    def existe_activa(self, id_usuario, id_experiencia):
        from apps.reservas.domain.policies import MaquinaEstadosReserva

        return any(
            r.usuario_id == id_usuario
            and r.experiencia_id == id_experiencia
            and MaquinaEstadosReserva.retiene_cupo(r.estado)
            for r in self.items
        )

    def existe_ticket(self, codigo_ticket):
        return self.obtener_por_ticket(codigo_ticket) is not None


class CatalogoFalso(CatalogoPort):
    """Simula el inventario de Catalogo y registra los movimientos de cupo."""

    def __init__(self, experiencia=None, cupo_disponible: int = 10):
        self.experiencia = experiencia
        self.cupo_disponible = cupo_disponible
        self.bloqueos: list[int] = []
        self.liberaciones: list[int] = []
        self.error_al_bloquear: Exception | None = None

    def obtener_experiencia(self, id_experiencia):
        return self.experiencia

    def bloquear_cupo(self, id_experiencia, cantidad):
        if self.error_al_bloquear is not None:
            raise self.error_al_bloquear
        self.cupo_disponible -= cantidad
        self.bloqueos.append(cantidad)

    def liberar_cupo(self, id_experiencia, cantidad):
        self.cupo_disponible += cantidad
        self.liberaciones.append(cantidad)


class PerfilFalso(PerfilUsuarioPort):
    def __init__(self, usuario=None):
        self.usuario = usuario

    def obtener(self, id_usuario):
        return self.usuario


class NotificadorEspia(NotificadorPort):
    """Registra los avisos emitidos sin enviar nada."""

    def __init__(self):
        self.eventos: list[str] = []

    def reserva_creada(self, reserva, usuario, experiencia):
        self.eventos.append("reserva_creada")

    def reserva_confirmada(self, reserva, usuario, experiencia):
        self.eventos.append("reserva_confirmada")

    def reserva_cancelada(self, reserva, usuario, reembolso):
        self.eventos.append("reserva_cancelada")
