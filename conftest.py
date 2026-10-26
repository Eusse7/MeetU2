"""
Arranca Django antes de recolectar las pruebas.

Los tests de la capa de aplicacion son unitarios: usan dobles de prueba en
lugar de los repositorios Django, por lo que no necesitan base de datos.
Aun asi Django debe estar configurado para poder importar las entidades.
"""
import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent
for service in ["pagos", "social", "notificaciones", "catalogo"]:
    service_path = str(BASE_DIR / "services" / service)
    if service_path not in sys.path:
        sys.path.insert(0, service_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
