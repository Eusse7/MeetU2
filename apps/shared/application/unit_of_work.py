"""
Unidad de Trabajo (Unit of Work) como puerto.

Un caso de uso necesita decir "esto es atomico" sin saber que hay un motor
transaccional de Django detras. Declararlo como abstraccion permite:

  * probar los servicios sin base de datos (los dobles usan `SinTransaccion`);
  * cambiar el mecanismo (transaccion SQL hoy, saga distribuida el dia que un
    contexto se extraiga a otro servicio) sin tocar la capa de aplicacion.

La implementacion concreta vive en `apps/shared/infrastructure/unit_of_work.py`.
"""
from abc import ABC, abstractmethod


class UnitOfWorkPort(ABC):
    """Delimita un bloque que se confirma entero o no se confirma."""

    @abstractmethod
    def __enter__(self) -> "UnitOfWorkPort": ...

    @abstractmethod
    def __exit__(self, tipo_exc, exc, traza) -> bool | None: ...


class SinTransaccion(UnitOfWorkPort):
    """
    Implementacion nula: ejecuta el bloque sin garantia transaccional.

    Es el valor por defecto en pruebas unitarias con repositorios en memoria,
    donde no hay nada que confirmar ni revertir.
    """

    def __enter__(self) -> "SinTransaccion":
        return self

    def __exit__(self, tipo_exc, exc, traza) -> None:
        return None
