"""
Errores del microservicio de Pagos.

Replican el contrato del monolito (`apps/shared/domain/exceptions.py`): todo
error sale como `{"error": {"codigo", "mensaje"}}` con su status HTTP. Asi el
front trata igual una respuesta de /api/v1 (Django) que una de /api/v2 (Flask)
y la migracion es invisible para el cliente.
"""


class PagoError(Exception):
    """Error de negocio. Mapea a 400."""

    codigo = "pago_error"
    status_code = 400

    def __init__(self, mensaje: str, codigo: str | None = None, detalle=None):
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo
        self.detalle = detalle
        super().__init__(mensaje)

    def como_dict(self) -> dict:
        cuerpo = {"codigo": self.codigo, "mensaje": self.mensaje}
        if self.detalle:
            cuerpo["detalle"] = self.detalle
        return {"error": cuerpo}


class DatosInvalidos(PagoError):
    codigo = "datos_pago_invalidos"
    status_code = 400


class PagoNoEncontrado(PagoError):
    codigo = "pago_no_encontrado"
    status_code = 404


class ReservaNoEncontrada(PagoError):
    codigo = "reserva_no_encontrada"
    status_code = 404


class PagoRechazado(PagoError):
    """La pasarela declino el cobro. 402 Payment Required."""

    codigo = "pago_rechazado"
    status_code = 402


class ConflictoPago(PagoError):
    """El estado actual impide la operacion. Mapea a 409."""

    codigo = "conflicto_pago"
    status_code = 409


class PagoDuplicado(ConflictoPago):
    codigo = "pago_duplicado"


class ReservaNoPagable(ConflictoPago):
    codigo = "reserva_no_pagable"


class UsuarioNoAutorizado(ConflictoPago):
    codigo = "usuario_no_autorizado"


class SinReembolso(ConflictoPago):
    codigo = "sin_reembolso"


class ServicioNoDisponible(PagoError):
    """Una dependencia (monolito o pasarela) no responde. 503."""

    codigo = "servicio_no_disponible"
    status_code = 503
