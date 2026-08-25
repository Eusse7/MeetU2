"""
Arranca Django antes de recolectar las pruebas.

Los tests de la capa de aplicacion son unitarios: usan dobles de prueba en
lugar de los repositorios Django, por lo que no necesitan base de datos.
Aun asi Django debe estar configurado para poder importar las entidades.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
