"""Controladores HTTP / API REST del microservicio Catalogo."""
from datetime import datetime, timezone
import uuid

from flask import Blueprint, current_app, jsonify, request

from catalogo_service.domain import Modalidad
from catalogo_service.errors import CupoExcedeAforoError, ExperienciaNoEncontradaError, UbicacionNoEncontradaError

catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/api/v2/catalogo")


def _exp_to_dict(exp):
    return {
        "id": str(exp.id),
        "organizador_id": str(exp.organizador_id),
        "categoria_id": str(exp.categoria_id),
        "ubicacion_id": str(exp.ubicacion_id),
        "titulo": exp.titulo,
        "descripcion": exp.descripcion,
        "precio_cop": exp.precio_cop,
        "cupo_maximo": exp.cupo_maximo,
        "cupos_disponibles": exp.cupos_disponibles,
        "fecha_evento": exp.fecha_evento.isoformat() if exp.fecha_evento else None,
        "modalidad": exp.modalidad.value,
        "estado": exp.estado.value,
        "creado_en": exp.creado_en.isoformat() if exp.creado_en else None,
    }


def _cat_to_dict(cat):
    return {
        "id": str(cat.id),
        "nombre": cat.nombre,
        "slug": cat.slug,
        "descripcion": cat.descripcion,
        "activa": cat.activa,
    }


def _ubi_to_dict(ubi):
    return {
        "id": str(ubi.id),
        "nombre": ubi.nombre,
        "direccion": ubi.direccion,
        "ciudad": ubi.ciudad,
        "latitud": ubi.latitud,
        "longitud": ubi.longitud,
        "aforo_maximo": ubi.aforo_maximo,
    }


@catalogo_bp.route("/salud", methods=["GET"])
def salud():
    return jsonify({
        "status": "ok",
        "servicio": "catalogo",
        "version": "v2",
        "patron": "microservicio_estrangulado",
    }), 200


@catalogo_bp.route("/categorias", methods=["GET"])
def listar_categorias():
    service = current_app.config["CATALOGO_SERVICE"]
    cats = service.listar_categorias()
    return jsonify([_cat_to_dict(c) for c in cats]), 200


@catalogo_bp.route("/categorias", methods=["POST"])
def crear_categoria():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    if not nombre:
        return jsonify({"error": "El campo 'nombre' es obligatorio"}), 400

    service = current_app.config["CATALOGO_SERVICE"]
    cat = service.crear_categoria(nombre=str(nombre), descripcion=str(data.get("descripcion", "")))
    return jsonify(_cat_to_dict(cat)), 201


@catalogo_bp.route("/ubicaciones", methods=["GET"])
def listar_ubicaciones():
    service = current_app.config["CATALOGO_SERVICE"]
    ubis = service.listar_ubicaciones()
    return jsonify([_ubi_to_dict(u) for u in ubis]), 200


@catalogo_bp.route("/ubicaciones", methods=["POST"])
def crear_ubicacion():
    data = request.get_json(silent=True) or {}
    requeridos = ["nombre", "direccion", "ciudad", "latitud", "longitud", "aforo_maximo"]
    for campo in requeridos:
        if campo not in data:
            return jsonify({"error": f"El campo '{campo}' es obligatorio"}), 400

    service = current_app.config["CATALOGO_SERVICE"]
    try:
        ubi = service.crear_ubicacion(
            nombre=str(data["nombre"]),
            direccion=str(data["direccion"]),
            ciudad=str(data["ciudad"]),
            latitud=float(data["latitud"]),
            longitud=float(data["longitud"]),
            aforo_maximo=int(data["aforo_maximo"]),
        )
        return jsonify(_ubi_to_dict(ubi)), 201
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@catalogo_bp.route("/experiencias", methods=["GET"])
def listar_experiencias():
    service = current_app.config["CATALOGO_SERVICE"]
    cat_id_str = request.args.get("categoria_id")
    precio_max_str = request.args.get("precio_max")

    cat_id = None
    if cat_id_str:
        try:
            cat_id = uuid.UUID(cat_id_str)
        except ValueError:
            return jsonify({"error": "categoria_id no es un UUID valido"}), 400

    precio_max = None
    if precio_max_str:
        try:
            precio_max = float(precio_max_str)
        except ValueError:
            return jsonify({"error": "precio_max no es numerico"}), 400

    exps = service.listar_experiencias(categoria_id=cat_id, precio_max=precio_max)
    return jsonify([_exp_to_dict(e) for e in exps]), 200


@catalogo_bp.route("/experiencias", methods=["POST"])
def crear_experiencia():
    data = request.get_json(silent=True) or {}
    requeridos = [
        "organizador_id",
        "categoria_id",
        "ubicacion_id",
        "titulo",
        "precio_cop",
        "cupo_maximo",
    ]
    for campo in requeridos:
        if campo not in data:
            return jsonify({"error": f"El campo '{campo}' es obligatorio"}), 400

    try:
        organizador_id = uuid.UUID(str(data["organizador_id"]))
        categoria_id = uuid.UUID(str(data["categoria_id"]))
        ubicacion_id = uuid.UUID(str(data["ubicacion_id"]))
        precio_cop = float(data["precio_cop"])
        cupo_maximo = int(data["cupo_maximo"])
        fecha_evento_str = data.get("fecha_evento")
        fecha_evento = (
            datetime.fromisoformat(fecha_evento_str)
            if fecha_evento_str
            else datetime.now(timezone.utc)
        )
        modalidad = Modalidad(data.get("modalidad", "PRESENCIAL"))
    except (ValueError, TypeError) as err:
        return jsonify({"error": f"Datos invalidos: {err}"}), 400

    service = current_app.config["CATALOGO_SERVICE"]
    try:
        exp = service.crear_experiencia(
            organizador_id=organizador_id,
            categoria_id=categoria_id,
            ubicacion_id=ubicacion_id,
            titulo=str(data["titulo"]),
            descripcion=str(data.get("descripcion", "")),
            precio_cop=precio_cop,
            cupo_maximo=cupo_maximo,
            fecha_evento=fecha_evento,
            modalidad=modalidad,
        )
        return jsonify(_exp_to_dict(exp)), 201
    except UbicacionNoEncontradaError as err:
        return jsonify({"error": str(err)}), 404
    except CupoExcedeAforoError as err:
        return jsonify({"error": str(err)}), 400


@catalogo_bp.route("/experiencias/<exp_id>", methods=["GET"])
def obtener_experiencia(exp_id):
    try:
        e_id = uuid.UUID(exp_id)
    except ValueError:
        return jsonify({"error": "ID no es un UUID valido"}), 400

    service = current_app.config["CATALOGO_SERVICE"]
    try:
        exp = service.obtener_experiencia(e_id)
        return jsonify(_exp_to_dict(exp)), 200
    except ExperienciaNoEncontradaError as err:
        return jsonify({"error": str(err)}), 404
