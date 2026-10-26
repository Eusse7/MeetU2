"""Inicializador de la aplicacion Flask del microservicio Catalogo."""
import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from catalogo_service.api import catalogo_bp
from catalogo_service.repository import Base, SQLAlchemyCatalogoRepository
from catalogo_service.services import CatalogoService


def create_app(database_url: str | None = None) -> Flask:
    app = Flask(__name__)

    db_url = (
        database_url
        or os.environ.get("CATALOGO_DATABASE_URL")
        or "sqlite:///catalogo_dev.db"
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

    repository = SQLAlchemyCatalogoRepository(session_factory=session_factory)
    service = CatalogoService(repository=repository)

    app.config["ENGINE"] = engine
    app.config["SESSION_FACTORY"] = session_factory
    app.config["CATALOGO_REPOSITORY"] = repository
    app.config["CATALOGO_SERVICE"] = service

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session_factory.remove()

    app.register_blueprint(catalogo_bp)
    return app
