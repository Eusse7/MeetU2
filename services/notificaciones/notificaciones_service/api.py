"""Controladores HTTP / API REST del microservicio de Notificaciones."""
import json
import uuid

from flask import Blueprint, current_app, jsonify, request

from notificaciones_service.domain import CanalNotificacion

notificaciones_bp = Blueprint("notificaciones", __name__, url_prefix="/api/v2/notificaciones")


def _notif_to_dict(notif):
    try:
        meta = json.loads(notif.metadata_envio)
    except Exception:
        meta = {}
    return {
        "id": str(notif.id),
        "usuario_id": str(notif.usuario_id),
        "canal": notif.canal.value,
        "destinatario": notif.destinatario,
        "asunto": notif.asunto,
        "mensaje": notif.mensaje,
        "estado": notif.estado.value,
        "metadata": meta,
        "creado_en": notif.creado_en.isoformat() if notif.creado_en else None,
    }


@notificaciones_bp.route("/salud", methods=["GET"])
def salud():
    return jsonify({
        "status": "ok",
        "servicio": "notificaciones",
        "version": "v2",
        "canales_soportados": ["email", "sms", "push", "asincrono"],
    }), 200


@notificaciones_bp.route("/enviar", methods=["POST"])
def enviar_notificacion():
    data = request.get_json(silent=True) or {}
    requeridos = ["usuario_id", "canal", "destinatario", "asunto", "mensaje"]
    for campo in requeridos:
        if campo not in data:
            return jsonify({"error": f"El campo '{campo}' es obligatorio"}), 400

    try:
        usuario_id = uuid.UUID(str(data["usuario_id"]))
        canal = CanalNotificacion(str(data["canal"]).lower())
    except ValueError as err:
        return jsonify({"error": f"Dato invalido: {err}"}), 400

    service = current_app.config["NOTIFICACIONES_SERVICE"]
    notif = service.despachar(
        usuario_id=usuario_id,
        canal=canal,
        destinatario=str(data["destinatario"]),
        asunto=str(data["asunto"]),
        mensaje=str(data["mensaje"]),
        metadata=data.get("metadata"),
    )
    return jsonify(_notif_to_dict(notif)), 201


@notificaciones_bp.route("/historial/<usuario_id>", methods=["GET"])
def historial(usuario_id):
    try:
        u_id = uuid.UUID(usuario_id)
    except ValueError:
        return jsonify({"error": "usuario_id no es un UUID valido"}), 400

    service = current_app.config["NOTIFICACIONES_SERVICE"]
    notifs = service.consultar_historial(u_id)
    return jsonify([_notif_to_dict(n) for n in notifs]), 200
