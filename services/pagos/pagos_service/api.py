"""
API REST del microservicio (prefijo /api/v2/pagos).

Solo traduce HTTP <-> casos de uso: valida la forma del JSON, arma el DTO y
serializa la respuesta. Los errores los convierte `errors_http.py`.

Rutas:
  GET  /api/v2/pagos/salud                          estado del servicio
  POST /api/v2/pagos                                cobrar una reserva      201
  GET  /api/v2/pagos?id_reserva=&id_usuario=        listar pagos            200
  GET  /api/v2/pagos/<id>                           detalle                 200
  GET  /api/v2/pagos/referencias/<referencia>       verificar comprobante   200
  POST /api/v2/pagos/reembolsos                     reembolsar cancelada    200
  GET  /api/v2/pagos/organizadores/<id>/liquidacion neto a desembolsar      200
"""
from uuid import UUID

from flask import Blueprint, current_app, jsonify, request

from pagos_service.errors import DatosInvalidos
from pagos_service.services import (
    ConsultarPagosService,
    LiquidacionOrganizadorService,
    ProcesarPagoDTO,
    ProcesarPagoService,
    ReembolsarPagoService,
)

bp = Blueprint("pagos", __name__, url_prefix="/api/v2/pagos")


# ------------------------------------------------------------------ helpers
def _cuerpo_json() -> dict:
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise DatosInvalidos(
            "El cuerpo debe ser un objeto JSON (Content-Type: application/json)",
            codigo="json_invalido",
        )
    return datos


def _uuid(valor, campo: str) -> UUID:
    try:
        return UUID(str(valor))
    except (TypeError, ValueError):
        raise DatosInvalidos(
            f"'{campo}' debe ser un UUID valido", codigo="datos_pago_invalidos",
            detalle={"campo": campo},
        ) from None


def _requerido(datos: dict, campo: str):
    if datos.get(campo) in (None, ""):
        raise DatosInvalidos(
            f"El campo '{campo}' es obligatorio", detalle={"campo": campo}
        )
    return datos[campo]


def _deps():
    return (
        current_app.extensions["pagos.repositorio"],
        current_app.extensions["pagos.pasarela"],
        current_app.extensions["pagos.reservas"],
    )


# -------------------------------------------------------------------- rutas
@bp.get("/salud")
def salud():
    return jsonify(
        {
            "status": "ok",
            "servicio": "meetu2-pagos",
            "framework": "flask",
            "pasarela": current_app.extensions["pagos.pasarela"].nombre,
        }
    )


@bp.post("")
def procesar_pago():
    datos = _cuerpo_json()
    dto = ProcesarPagoDTO(
        id_reserva=_uuid(_requerido(datos, "id_reserva"), "id_reserva"),
        id_usuario=_uuid(_requerido(datos, "id_usuario"), "id_usuario"),
        medio_pago=str(_requerido(datos, "medio_pago")),
        token_pago=str(datos.get("token_pago", "")),
    )
    repo, pasarela, reservas = _deps()
    pago = ProcesarPagoService(repo, pasarela, reservas).ejecutar(dto)
    return jsonify(pago.como_dict()), 201


@bp.get("")
def listar_pagos():
    filtros = {}
    for campo in ("id_reserva", "id_usuario", "id_organizador"):
        if request.args.get(campo):
            filtros[campo] = _uuid(request.args[campo], campo)
    repo, _, _ = _deps()
    pagos = ConsultarPagosService(repo).listar(**filtros)
    return jsonify([p.como_dict() for p in pagos])


@bp.get("/<id_pago>")
def detalle_pago(id_pago):
    repo, _, _ = _deps()
    pago = ConsultarPagosService(repo).por_id(_uuid(id_pago, "id_pago"))
    return jsonify(pago.como_dict())


@bp.get("/referencias/<referencia>")
def pago_por_referencia(referencia):
    repo, _, _ = _deps()
    return jsonify(ConsultarPagosService(repo).por_referencia(referencia).como_dict())


@bp.post("/reembolsos")
def reembolsar():
    datos = _cuerpo_json()
    id_reserva = _uuid(_requerido(datos, "id_reserva"), "id_reserva")
    repo, pasarela, reservas = _deps()
    pago = ReembolsarPagoService(repo, pasarela, reservas).ejecutar(id_reserva)
    return jsonify(pago.como_dict())


@bp.get("/organizadores/<id_organizador>/liquidacion")
def liquidacion(id_organizador):
    repo, _, _ = _deps()
    resumen = LiquidacionOrganizadorService(repo).ejecutar(
        _uuid(id_organizador, "id_organizador")
    )
    return jsonify(resumen)
