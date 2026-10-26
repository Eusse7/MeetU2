"""Inicializador de la aplicacion Flask del microservicio de Notificaciones."""
import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from notificaciones_service.api import notificaciones_bp
from notificaciones_service.gateways import SenderRegistry
from notificaciones_service.repository import Base, SQLAlchemyNotificacionRepository
from notificaciones_service.services import NotificacionesService


def create_app(database_url: str | None = None) -> Flask:
    app = Flask(__name__)

    db_url = (
        database_url
        or os.environ.get("NOTIFICACIONES_DATABASE_URL")
        or "sqlite:///notificaciones_dev.db"
    )
    engine_kwargs = {}
    if db_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in db_url:
            from sqlalchemy.pool import StaticPool
            engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(db_url, **engine_kwargs)
    session_factory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    Base.metadata.create_all(bind=engine)

    repository = SQLAlchemyNotificacionRepository(session_factory=session_factory)
    sender_registry = SenderRegistry()
    service = NotificacionesService(repository=repository, sender_registry=sender_registry)

    app.config["ENGINE"] = engine
    app.config["SESSION_FACTORY"] = session_factory
    app.config["NOTIFICACIONES_REPOSITORY"] = repository
    app.config["NOTIFICACIONES_SERVICE"] = service

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session_factory.remove()

    app.register_blueprint(notificaciones_bp)
    return app
