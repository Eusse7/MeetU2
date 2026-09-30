"""
Manejo centralizado de errores: resiliencia del microservicio.

Ninguna excepcion sale como pagina HTML ni como traza: todo se convierte en
JSON estructurado `{"error": {"codigo", "mensaje"}}`.

  PagoError (negocio)      -> su status (400/402/404/409/503)
  HTTPException (Flask)    -> su status (404 ruta, 405 metodo, 415...)
  Exception (inesperada)   -> 500 sin filtrar detalles internos
"""
import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from pagos_service.errors import PagoError

log = logging.getLogger("pagos")


def registrar_manejadores(app: Flask) -> None:
    @app.errorhandler(PagoError)
    def _negocio(exc: PagoError):
        if exc.status_code >= 500:
            log.warning("Dependencia no disponible: %s", exc.mensaje)
        return jsonify(exc.como_dict()), exc.status_code

    @app.errorhandler(HTTPException)
    def _http(exc: HTTPException):
        codigo = (exc.name or "error_http").lower().replace(" ", "_")
        return (
            jsonify({"error": {"codigo": codigo, "mensaje": exc.description}}),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def _inesperado(exc: Exception):
        log.exception("Error no controlado en el microservicio de pagos")
        return (
            jsonify(
                {
                    "error": {
                        "codigo": "error_interno",
                        "mensaje": "Ocurrio un error inesperado procesando el pago",
                    }
                }
            ),
            500,
        )
