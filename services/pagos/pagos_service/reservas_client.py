"""
Anti-Corruption Layer hacia el monolito.

El microservicio NO lee la tabla `reservas_reserva`: le pregunta a Django por
HTTP (/api/v1/reservas/...). Asi el monolito sigue siendo el dueno de las
reservas y el esquema de su base de datos puede cambiar sin romper Pagos.

Todo lo que viene de Django se traduce a `ReservaVista`, la proyeccion minima
que Pagos necesita para decidir.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import requests

from pagos_service.errors import (
    ConflictoPago,
    ReservaNoEncontrada,
    ServicioNoDisponible,
)


@dataclass(frozen=True)
class ReservaVista:
    id: UUID
    usuario_id: UUID
    organizador_id: UUID
    estado: str
    monto_total: Decimal
    comision_plataforma: Decimal
    monto_reembolsado: Decimal
    codigo_ticket: str = ""


class ReservasPort(ABC):
    @abstractmethod
    def obtener(self, id_reserva: UUID) -> ReservaVista: ...

    @abstractmethod
    def confirmar(self, id_reserva: UUID, referencia_pago: str) -> None: ...


class ReservasHttpClient(ReservasPort):
    def __init__(self, url_base: str, timeout: float = 5.0):
        self._url = url_base.rstrip("/")
        self._timeout = timeout

    def obtener(self, id_reserva: UUID) -> ReservaVista:
        respuesta = self._llamar(
            "get", f"/api/v1/reservas/reservas/{id_reserva}"
        )
        if respuesta.status_code == 404:
            raise ReservaNoEncontrada(f"No existe la reserva {id_reserva}")
        self._exigir_ok(respuesta)
        datos = respuesta.json()
        return ReservaVista(
            id=UUID(datos["id"]),
            usuario_id=UUID(datos["usuario_id"]),
            organizador_id=UUID(datos["organizador_id"]),
            estado=datos["estado"],
            monto_total=Decimal(str(datos["monto_total"])),
            comision_plataforma=Decimal(str(datos["comision_plataforma"])),
            monto_reembolsado=Decimal(str(datos["monto_reembolsado"])),
            codigo_ticket=datos.get("codigo_ticket", ""),
        )

    def confirmar(self, id_reserva: UUID, referencia_pago: str) -> None:
        respuesta = self._llamar(
            "post",
            f"/api/v1/reservas/reservas/{id_reserva}/confirmacion",
            json={"referencia_pago": referencia_pago},
        )
        if respuesta.status_code in (404, 409):
            error = self._error_de(respuesta)
            raise ConflictoPago(
                f"El monolito rechazo la confirmacion: {error.get('mensaje', '')}",
                codigo=error.get("codigo", "confirmacion_rechazada"),
            )
        self._exigir_ok(respuesta)

    # ----------------------------------------------------------- internos
    def _llamar(self, metodo: str, ruta: str, **kwargs) -> requests.Response:
        try:
            return requests.request(
                metodo, f"{self._url}{ruta}", timeout=self._timeout, **kwargs
            )
        except requests.RequestException as exc:
            raise ServicioNoDisponible(
                "El monolito de reservas no responde; intenta de nuevo",
                detalle=type(exc).__name__,
            ) from exc

    @staticmethod
    def _error_de(respuesta: requests.Response) -> dict:
        try:
            return respuesta.json().get("error", {}) or {}
        except ValueError:
            return {}

    def _exigir_ok(self, respuesta: requests.Response) -> None:
        if respuesta.status_code >= 400:
            raise ServicioNoDisponible(
                f"Respuesta inesperada del monolito ({respuesta.status_code})",
                detalle=self._error_de(respuesta) or None,
            )
