"""
Reglas de negocio puras del contexto Catalogo.

No importan Django ni conocen la persistencia: reciben datos primitivos y
devuelven decisiones. Esto las hace testeables sin base de datos y evita que la
logica termine dentro de los modelos (Fat Models) o de las vistas (Fat Views).
"""
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from apps.catalogo.domain.enums import EstadoExperiencia
from apps.catalogo.domain.exceptions import (
    AforoExcedido,
    DatosExperienciaInvalidos,
    TransicionExperienciaInvalida,
)

CENTAVOS = Decimal("0.01")

# Una experiencia debe publicarse con antelacion suficiente para ser reservable.
ANTELACION_MINIMA = timedelta(hours=2)
CUPO_MINIMO = 1
CUPO_MAXIMO_ABSOLUTO = 500


class PoliticaAforo:
    """La ubicacion manda sobre cuanta gente cabe."""

    @staticmethod
    def validar(cupo_maximo: int, aforo_ubicacion: int | None) -> None:
        if cupo_maximo < CUPO_MINIMO:
            raise DatosExperienciaInvalidos(
                f"El cupo maximo debe ser al menos {CUPO_MINIMO}"
            )
        if cupo_maximo > CUPO_MAXIMO_ABSOLUTO:
            raise DatosExperienciaInvalidos(
                f"El cupo maximo no puede superar {CUPO_MAXIMO_ABSOLUTO}"
            )
        if aforo_ubicacion is not None and cupo_maximo > aforo_ubicacion:
            raise AforoExcedido(
                f"El cupo solicitado ({cupo_maximo}) supera el aforo de la "
                f"ubicacion ({aforo_ubicacion})"
            )

    @staticmethod
    def hay_disponibilidad(cupo_disponible: int, cantidad: int) -> bool:
        return cantidad > 0 and cupo_disponible >= cantidad


class PoliticaAgenda:
    """Cuando puede ocurrir una experiencia."""

    @staticmethod
    def validar_fecha(fecha_hora: datetime, ahora: datetime) -> None:
        if fecha_hora <= ahora:
            raise DatosExperienciaInvalidos(
                "La fecha de la experiencia debe estar en el futuro"
            )
        if fecha_hora - ahora < ANTELACION_MINIMA:
            raise DatosExperienciaInvalidos(
                "La experiencia debe publicarse con al menos 2 horas de antelacion"
            )


class CalculadoraPrecio:
    """Aritmetica monetaria del catalogo."""

    @staticmethod
    def normalizar(precio: Decimal) -> Decimal:
        if precio < 0:
            raise DatosExperienciaInvalidos("El precio no puede ser negativo")
        return Decimal(precio).quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    @staticmethod
    def calcular_precio_final(
        precio_base: Decimal, descuento_porcentaje: Decimal = Decimal("0")
    ) -> Decimal:
        if not Decimal("0") <= descuento_porcentaje <= Decimal("1"):
            raise DatosExperienciaInvalidos(
                "El descuento debe expresarse entre 0 y 1"
            )
        neto = Decimal(precio_base) * (Decimal("1") - descuento_porcentaje)
        return neto.quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    @staticmethod
    def calcular_recaudo_total(precio: Decimal, cupos_vendidos: int) -> Decimal:
        return (Decimal(precio) * cupos_vendidos).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP
        )


class CicloVidaExperiencia:
    """Maquina de estados: solo permite transiciones legales."""

    TRANSICIONES: dict[str, set[str]] = {
        EstadoExperiencia.BORRADOR: {
            EstadoExperiencia.PUBLICADA,
            EstadoExperiencia.CANCELADA,
        },
        EstadoExperiencia.PUBLICADA: {
            EstadoExperiencia.AGOTADA,
            EstadoExperiencia.CANCELADA,
            EstadoExperiencia.FINALIZADA,
        },
        EstadoExperiencia.AGOTADA: {
            EstadoExperiencia.PUBLICADA,
            EstadoExperiencia.CANCELADA,
            EstadoExperiencia.FINALIZADA,
        },
        EstadoExperiencia.CANCELADA: set(),
        EstadoExperiencia.FINALIZADA: set(),
    }

    @classmethod
    def validar_transicion(cls, actual: str, nuevo: str) -> None:
        if nuevo not in cls.TRANSICIONES.get(actual, set()):
            raise TransicionExperienciaInvalida(
                f"No se puede pasar de {actual} a {nuevo}"
            )

    @staticmethod
    def es_reservable(estado: str) -> bool:
        return estado == EstadoExperiencia.PUBLICADA


class PoliticaAfinidad:
    """
    Puntua que tan bien encaja una experiencia con los intereses del usuario.

    Es el corazon de la propuesta de valor (encontrar gente afin), por eso vive
    en el dominio y no escondida en un queryset.
    """

    @staticmethod
    def calcular_coincidencia(
        intereses_usuario: dict[str, int], categorias_experiencia: set[str]
    ) -> float:
        if not intereses_usuario or not categorias_experiencia:
            return 0.0

        comunes = categorias_experiencia & set(intereses_usuario)
        if not comunes:
            return 0.0

        # Media de los niveles de afinidad declarados (1..5) ponderada por la
        # cobertura de las categorias de la experiencia.
        suma_niveles = sum(intereses_usuario[cat] for cat in comunes)
        nivel_medio = suma_niveles / (len(comunes) * 5)
        cobertura = len(comunes) / len(categorias_experiencia)
        return round(nivel_medio * cobertura, 4)
