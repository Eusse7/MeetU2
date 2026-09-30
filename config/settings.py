"""
Configuracion del monolito modular MeetU2.

Los valores sensibles y los que cambian por entorno se leen de variables de
entorno (.env). Las constantes de negocio viven aqui para poder inyectarlas en
la capa de aplicacion sin que los servicios dependan de Django.
"""
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(clave: str, defecto: bool = False) -> bool:
    return os.environ.get(clave, str(defecto)).strip().lower() in {"1", "true", "yes"}


def env_list(clave: str, defecto: str = "") -> list[str]:
    crudo = os.environ.get(clave, defecto)
    return [item.strip() for item in crudo.split(",") if item.strip()]


# ---------------------------------------------------------------- Seguridad
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-&-ae3@13h*enjh3_db@+6xy7*w4m4ht_5bpcmu0c&c1=+f7w!#",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Detras de Nginx el navegador ve el origen del proxy, no el de Django.
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")


# ------------------------------------------------------------- Aplicaciones
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
]

# Un modulo por contexto acotado (bounded context). El orden refleja la
# direccion de las dependencias: shared <- identidad <- catalogo <- reservas.
# Pagos ya no vive aqui: se estrangulo hacia el microservicio Flask
# `services/pagos` (ver docs/wiki/Migración-a-Microservicios-(Strangler-Pattern).md).
LOCAL_APPS = [
    "apps.shared",
    "apps.identidad",
    "apps.catalogo",
    "apps.reservas",
    "apps.social",
    "apps.notificaciones",
    "apps.frontend",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.frontend.context_processors.feature_flags",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ------------------------------------------------------------ Base de datos
# SQLite en desarrollo; PostgreSQL cuando corre en docker-compose.
if os.environ.get("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "NAME": os.environ.get("POSTGRES_DB", "meetu2"),
            "USER": os.environ.get("POSTGRES_USER", "meetu2"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ------------------------------------------------------- Internacionalizacion
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------- Archivos static
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# ------------------------------------------------------------------- Correo
# Django 6.1 sustituye EMAIL_BACKEND por MAILERS.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
DEFAULT_FROM_EMAIL = "no-responder@meetu2.co"


# ---------------------------------------------------------------------- DRF
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.shared.api.exception_handler.domain_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.shared.api.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}


# ------------------------------------------------- Seleccion de implementacion
# Las lee la Factory correspondiente; cambiar el canal o la pasarela no
# requiere tocar ni un solo servicio de la capa de aplicacion.
CANAL_NOTIFICACION_DEFECTO = os.environ.get("CANAL_NOTIFICACION", "consola")


# ------------------------------------------------ Strangler Pattern: Pagos
# URL interna del microservicio Flask. Si esta definida, confirmar una reserva
# exige una referencia de pago APROBADO en ese servicio.
PAGOS_SERVICE_URL = os.environ.get("PAGOS_SERVICE_URL", "").strip()
# El front usa /api/v2/pagos (servido por Nginx -> Flask) cuando esta activo.
PAGOS_V2_HABILITADO = env_bool("PAGOS_V2_HABILITADO", bool(PAGOS_SERVICE_URL))


# ------------------------------------------------------- Reglas de negocio
# Parametros que la capa de aplicacion inyecta en las politicas de dominio.
COMISION_PLATAFORMA = Decimal(os.environ.get("COMISION_PLATAFORMA", "0.10"))
MINUTOS_EXPIRACION_RESERVA = int(os.environ.get("MINUTOS_EXPIRACION_RESERVA", "30"))
MAX_CUPOS_POR_RESERVA = int(os.environ.get("MAX_CUPOS_POR_RESERVA", "5"))
HORAS_VENTANA_CHECKIN = int(os.environ.get("HORAS_VENTANA_CHECKIN", "3"))
