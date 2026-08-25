"""Implementacion de la Unidad de Trabajo sobre transacciones de Django."""
from django.db import transaction

from apps.shared.application.unit_of_work import UnitOfWorkPort


class DjangoUnitOfWork(UnitOfWorkPort):
    """
    Envuelve `transaction.atomic()`.

    Si el bloque lanza, la transaccion se revierte: es lo que garantiza que un
    cupo bloqueado en Catalogo no quede huerfano cuando falla el guardado de la
    reserva que lo motivo.
    """

    def __enter__(self) -> "DjangoUnitOfWork":
        self._atomica = transaction.atomic()
        self._atomica.__enter__()
        return self

    def __exit__(self, tipo_exc, exc, traza) -> bool | None:
        return self._atomica.__exit__(tipo_exc, exc, traza)
