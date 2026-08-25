# apps/shared/application/unit_of_work.py
from contextlib import contextmanager

from django.db import transaction


@contextmanager
def unit_of_work():
    """Agrupa varias operaciones en una transacción atómica."""
    with transaction.atomic():
        yield