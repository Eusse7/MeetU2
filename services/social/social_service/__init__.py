"""Inicializador de la aplicacion Flask del microservicio Social."""
import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from social_service.api import social_bp
from social_service.repository import Base, SQLAlchemyResenaRepository
from social_service.reservas_client import ReservasClient
from social_service.services import SocialService


def create_app(database_url: str | None = None, monolito_url: str | None = None) -> Flask:
    app = Flask(__name__)

    db_url = (
        database_url
        or os.environ.get("SOCIAL_DATABASE_URL")
        or "sqlite:///social_dev.db"
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

    mono_url = monolito_url or os.environ.get("MONOLITO_URL", "")
    reservas_client = ReservasClient(monolito_url=mono_url)
    repository = SQLAlchemyResenaRepository(session_factory=session_factory)
    social_service = SocialService(repository=repository, reservas_client=reservas_client)

    app.config["ENGINE"] = engine
    app.config["SESSION_FACTORY"] = session_factory
    app.config["SOCIAL_REPOSITORY"] = repository
    app.config["SOCIAL_SERVICE"] = social_service

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session_factory.remove()

    app.register_blueprint(social_bp)
    return app
