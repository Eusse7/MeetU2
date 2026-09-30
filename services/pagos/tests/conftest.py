"""
Fixtures del microservicio.

El monolito se reemplaza por `MonolitoFalso` (implementa `ReservasPort`), asi
las pruebas no necesitan Django corriendo. La base de datos es un SQLite
temporal por prueba.
"""
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from pagos_service import create_app
from pagos_service.errors import ConflictoPago, ReservaNoEncontrada
from pagos_service.gateways import FakeGateway
from pagos_service.repository import SqlPagoRepository
from pagos_service.reservas_client import ReservaVista, ReservasPort

ID_USUARIO = UUID("11111111-1111-1111-1111-111111111111")
ID_ORGANIZADOR = UUID("22222222-2222-2222-2222-222222222222")


class MonolitoFalso(ReservasPort):
    """Doble del monolito Django: guarda reservas en memoria."""

    def __init__(self):
        self.reservas: dict[UUID, ReservaVista] = {}
        self.confirmaciones: list[tuple[UUID, str]] = []
        self.rechazar_confirmacion = False

    def agregar(self, monto="90000.00", comision="9000.00", estado="PENDIENTE_PAGO",
                reembolsado="0.00") -> ReservaVista:
        reserva = ReservaVista(
            id=uuid4(),
            usuario_id=ID_USUARIO,
            organizador_id=ID_ORGANIZADOR,
            estado=estado,
            monto_total=Decimal(monto),
            comision_plataforma=Decimal(comision),
            monto_reembolsado=Decimal(reembolsado),
        )
        self.reservas[reserva.id] = reserva
        return reserva

    def cambiar(self, id_reserva, **campos):
        actual = self.reservas[id_reserva]
        self.reservas[id_reserva] = ReservaVista(**{**actual.__dict__, **campos})

    def obtener(self, id_reserva):
        if id_reserva not in self.reservas:
            raise ReservaNoEncontrada(f"No existe la reserva {id_reserva}")
        return self.reservas[id_reserva]

    def confirmar(self, id_reserva, referencia_pago):
        if self.rechazar_confirmacion:
            raise ConflictoPago("La ventana de pago expiro", codigo="reserva_expirada")
        self.confirmaciones.append((id_reserva, referencia_pago))
        self.cambiar(id_reserva, estado="CONFIRMADA")


@pytest.fixture
def monolito():
    return MonolitoFalso()


@pytest.fixture
def repo(tmp_path):
    return SqlPagoRepository.desde_url(f"sqlite:///{tmp_path / 'pagos.sqlite3'}")


@pytest.fixture
def app(repo, monolito):
    app = create_app(
        {"TESTING": True, "REPOSITORIO": repo, "PASARELA": FakeGateway(),
         "RESERVAS": monolito}
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()
