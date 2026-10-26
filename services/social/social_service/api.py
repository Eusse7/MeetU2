"""Controladores HTTP / API REST del microservicio Social."""
import uuid

from flask import Blueprint, current_app, jsonify, request

from social_service.domain import EstadoResena
from social_service.errors import (
    CalificacionInvalidaError,
    ResenaNoEncontradaError,
    ResenaYaExisteError,
    ReservaNoAptaError,
)

social_bp = Blueprint("social", __name__, url_prefix="/api/v2/social")


def _resena_to_dict(resena):
    return {
        "id": str(resena.id),
        "reserva_id": str(resena.reserva_id),
        "usuario_id": str(resena.usuario_id),
        "experiencia_id": str(resena.experiencia_id),
        "organizador_id": str(resena.organizador_id),
        "calificacion": resena.calificacion,
        "comentario": resena.comentario,
        "estado": resena.estado.value,
        "creado_en": resena.creado_en.isoformat() if resena.creado_en else None,
    }


@social_bp.route("/salud", methods=["GET"])
def salud():
    return jsonify({
        "status": "ok",
        "servicio": "social",
        "version": "v2",
        "patron": "microservicio_estrangulado",
    }), 200


@social_bp.route("/resenas", methods=["POST"])
def crear_resena():
    data = request.get_json(silent=True) or {}
    requeridos = ["reserva_id", "usuario_id", "experiencia_id", "organizador_id", "calificacion"]
    for campo in requeridos:
        if campo not in data:
            return jsonify({"error": f"El campo '{campo}' es obligatorio"}), 400

    try:
        reserva_id = uuid.UUID(str(data["reserva_id"]))
        usuario_id = uuid.UUID(str(data["usuario_id"]))
        experiencia_id = uuid.UUID(str(data["experiencia_id"]))
        organizador_id = uuid.UUID(str(data["organizador_id"]))
        calificacion = int(data["calificacion"])
        comentario = str(data.get("comentario", ""))
    except (ValueError, TypeError) as err:
        return jsonify({"error": f"Formato de datos invalido: {err}"}), 400

    service = current_app.config["SOCIAL_SERVICE"]
    try:
        resena = service.crear_resena(
            reserva_id=reserva_id,
            usuario_id=usuario_id,
            experiencia_id=experiencia_id,
            organizador_id=organizador_id,
            calificacion=calificacion,
            comentario=comentario,
            verificar_checkin=data.get("verificar_checkin", True),
        )
        return jsonify(_resena_to_dict(resena)), 201
    except CalificacionInvalidaError as err:
        return jsonify({"error": str(err)}), 400
    except ResenaYaExisteError as err:
        return jsonify({"error": str(err)}), 409
    except ReservaNoAptaError as err:
        return jsonify({"error": str(err)}), 400


@social_bp.route("/resenas", methods=["GET"])
def listar_resenas():
    service = current_app.config["SOCIAL_SERVICE"]
    experiencia_id_str = request.args.get("experiencia_id")
    organizador_id_str = request.args.get("organizador_id")

    if experiencia_id_str:
        try:
            exp_id = uuid.UUID(experiencia_id_str)
            resenas = service.listar_resenas_experiencia(exp_id)
            return jsonify([_resena_to_dict(r) for r in resenas]), 200
        except ValueError:
            return jsonify({"error": "experiencia_id no es un UUID valido"}), 400

    if organizador_id_str:
        try:
            org_id = uuid.UUID(organizador_id_str)
            resenas = service.listar_resenas_organizador(org_id)
            return jsonify([_resena_to_dict(r) for r in resenas]), 200
        except ValueError:
            return jsonify({"error": "organizador_id no es un UUID valido"}), 400

    return jsonify({"error": "Debe especificar experiencia_id u organizador_id"}), 400


@social_bp.route("/organizadores/<organizador_id>/reputacion", methods=["GET"])
def obtener_reputacion(organizador_id):
    try:
        org_id = uuid.UUID(organizador_id)
    except ValueError:
        return jsonify({"error": "organizador_id no es un UUID valido"}), 400

    service = current_app.config["SOCIAL_SERVICE"]
    rep = service.obtener_reputacion_organizador(org_id)
    return jsonify({
        "organizador_id": str(rep.organizador_id),
        "promedio": rep.promedio,
        "total_resenas": rep.total_resenas,
    }), 200
