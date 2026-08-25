# apps/identidad/application/dtos.py
from dataclasses import dataclass


@dataclass(frozen=True)
class RegistrarUsuarioDTO:
    nombre: str
    correo: str


@dataclass(frozen=True)
class ConvertirEnOrganizadorDTO:
    id_usuario: str
    nombre_comercial: str
    cuenta_bancaria: str = ""