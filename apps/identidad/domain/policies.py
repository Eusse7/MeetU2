"""
Reglas de negocio puras del contexto Identidad.

Se sacaron deliberadamente de los modelos: un `@property` que decide si un
organizador puede publicar es una regla de negocio, no persistencia.
"""
import re

from apps.identidad.domain.exceptions import DatosPerfilInvalidos
from apps.shared.domain.enums import EstadoValidacion

NOMBRE_MINIMO = 2
NIVEL_AFINIDAD_MIN = 1
NIVEL_AFINIDAD_MAX = 5

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


class PoliticaRegistro:
    """Que se considera un alta valida."""

    @staticmethod
    def normalizar_correo(correo: str) -> str:
        limpio = (correo or "").strip().lower()
        if not _CORREO.match(limpio):
            raise DatosPerfilInvalidos(f"El correo {correo!r} no es valido")
        return limpio

    @staticmethod
    def normalizar_nombre(nombre: str) -> str:
        limpio = " ".join((nombre or "").split())
        if len(limpio) < NOMBRE_MINIMO:
            raise DatosPerfilInvalidos(
                f"El nombre debe tener al menos {NOMBRE_MINIMO} caracteres"
            )
        return limpio


class PoliticaVerificacion:
    """Que habilita a un organizador frente a la plataforma."""

    @staticmethod
    def puede_publicar(estado_verificacion: str) -> bool:
        return estado_verificacion == EstadoValidacion.VERIFICADO

    @staticmethod
    def puede_recibir_desembolsos(estado_verificacion: str, cuenta: str) -> bool:
        return (
            PoliticaVerificacion.puede_publicar(estado_verificacion)
            and bool((cuenta or "").strip())
        )

    @staticmethod
    def resolver_estado(aprobado: bool) -> str:
        return EstadoValidacion.VERIFICADO if aprobado else EstadoValidacion.RECHAZADO


class PoliticaIntereses:
    """Valida el nivel de afinidad declarado por el usuario."""

    @staticmethod
    def validar_nivel(nivel: int) -> int:
        if not NIVEL_AFINIDAD_MIN <= nivel <= NIVEL_AFINIDAD_MAX:
            raise DatosPerfilInvalidos(
                f"El nivel de afinidad debe estar entre {NIVEL_AFINIDAD_MIN} "
                f"y {NIVEL_AFINIDAD_MAX}"
            )
        return nivel
