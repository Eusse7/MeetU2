"""Objetos de transferencia del contexto Identidad."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegistrarUsuarioDTO:
    nombre: str
    correo: str


@dataclass(frozen=True)
class ConvertirEnOrganizadorDTO:
    id_usuario: UUID
    nombre_comercial: str
    cuenta_bancaria: str = ""


@dataclass(frozen=True)
class VincularInteresDTO:
    id_usuario: UUID
    id_categoria: UUID
    nivel_afinidad: int = 3
