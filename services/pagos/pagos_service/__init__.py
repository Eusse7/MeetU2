"""
Microservicio de Pagos de MeetU2 (Flask).

Primer modulo estrangulado del monolito Django siguiendo el Strangler Pattern:
Nginx enruta /api/v2/pagos/ aqui y el resto del trafico sigue yendo a Django.
"""
import logging
import os

from flask import Flask

from pagos_service.api import bp
from pagos_service.errors_http import registrar_manejadores
from pagos_service.gateways import PasarelaFactory
from pagos_service.repository import SqlPagoRepository
from pagos_service.reservas_client import ReservasHttpClient


def create_app(config: dict | None = None) -> Flask:
    """
    Application Factory. Es el Composition Root del microservicio: aqui (y
    solo aqui) se eligen las implementaciones concretas de cada puerto.
    """
    app = Flask(__name__)
    app.config.update(
        DATABASE_URL=os.environ.get("PAGOS_DATABASE_URL", "sqlite:///pagos.sqlite3"),
        PASARELA_PAGO=os.environ.get("PASARELA_PAGO", "fake"),
        MONOLITO_URL=os.environ.get("MONOLITO_URL", "http://127.0.0.1:8000"),
        MONOLITO_TIMEOUT=float(os.environ.get("MONOLITO_TIMEOUT", "5")),
    )
    app.config.update(config or {})
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    logging.basicConfig(level=logging.INFO)

    app.extensions["pagos.repositorio"] = app.config.get(
        "REPOSITORIO"
    ) or SqlPagoRepository.desde_url(app.config["DATABASE_URL"])
    app.extensions["pagos.pasarela"] = app.config.get(
        "PASARELA"
    ) or PasarelaFactory.crear(app.config["PASARELA_PAGO"])
    app.extensions["pagos.reservas"] = app.config.get(
        "RESERVAS"
    ) or ReservasHttpClient(app.config["MONOLITO_URL"], app.config["MONOLITO_TIMEOUT"])

    registrar_manejadores(app)
    app.register_blueprint(bp)
    return app
