"""
Pasarelas de pago intercambiables + Factory.

Es la Factory que el README del monolito dejo prevista para la Entrega 2
(`PASARELA_PAGO=fake|wompi`), ahora viviendo dentro del microservicio: cambiar
de pasarela es una variable de entorno y no toca ni el servicio ni Django.
"""
import hashlib
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from pagos_service.errors import DatosInvalidos

# Tokens de prueba al estilo de los sandbox reales (Stripe, Wompi).
TOKEN_RECHAZADO = "tok_rechazada"
TOKEN_FONDOS_INSUFICIENTES = "tok_fondos_insuficientes"


@dataclass(frozen=True)
class ResultadoCobro:
    aprobado: bool
    referencia_pasarela: str
    motivo: str = ""


class PasarelaPort(ABC):
    nombre: str = ""

    @abstractmethod
    def cobrar(self, referencia: str, monto: Decimal, medio: str,
               token: str) -> ResultadoCobro: ...

    @abstractmethod
    def reembolsar(self, referencia_pasarela: str, monto: Decimal) -> str:
        """Devuelve la referencia del reembolso en la pasarela."""


class FakeGateway(PasarelaPort):
    """
    Pasarela en memoria para desarrollo y demo.

    Aprueba todo salvo los tokens de prueba de rechazo, asi se puede mostrar el
    camino 402 en la sustentacion sin depender de un tercero.
    """

    nombre = "fake"

    def cobrar(self, referencia, monto, medio, token) -> ResultadoCobro:
        token = (token or "").strip()
        if token == TOKEN_RECHAZADO:
            return ResultadoCobro(False, self._id("FAKE"), "Tarjeta rechazada por el emisor")
        if token == TOKEN_FONDOS_INSUFICIENTES:
            return ResultadoCobro(False, self._id("FAKE"), "Fondos insuficientes")
        return ResultadoCobro(True, self._id("FAKE"))

    def reembolsar(self, referencia_pasarela, monto) -> str:
        return self._id("FAKE-RF")

    @staticmethod
    def _id(prefijo: str) -> str:
        return f"{prefijo}-{secrets.token_hex(6).upper()}"


class WompiSandboxGateway(FakeGateway):
    """
    Simulacion del sandbox de Wompi.

    Reproduce su forma de referencia (firma de integridad SHA-256 sobre
    referencia+monto en centavos+moneda) sin salir a internet. Conectar la API
    real es reemplazar `cobrar`/`reembolsar` por llamadas HTTP; el resto del
    microservicio no se entera.
    """

    nombre = "wompi"

    def __init__(self, secreto_integridad: str = "test_integrity_secret"):
        self._secreto = secreto_integridad

    def cobrar(self, referencia, monto, medio, token) -> ResultadoCobro:
        resultado = super().cobrar(referencia, monto, medio, token)
        centavos = int(Decimal(monto) * 100)
        firma = hashlib.sha256(
            f"{referencia}{centavos}COP{self._secreto}".encode()
        ).hexdigest()[:16].upper()
        return ResultadoCobro(resultado.aprobado, f"WMP-{firma}", resultado.motivo)

    def reembolsar(self, referencia_pasarela, monto) -> str:
        return f"WMP-RF-{secrets.token_hex(6).upper()}"


class PasarelaFactory:
    _registro: dict[str, type[PasarelaPort]] = {
        FakeGateway.nombre: FakeGateway,
        WompiSandboxGateway.nombre: WompiSandboxGateway,
    }

    @classmethod
    def crear(cls, nombre: str) -> PasarelaPort:
        clase = cls._registro.get((nombre or "").strip().lower())
        if clase is None:
            raise DatosInvalidos(
                f"Pasarela '{nombre}' no soportada. "
                f"Opciones: {', '.join(sorted(cls._registro))}",
                codigo="pasarela_invalida",
            )
        return clase()
