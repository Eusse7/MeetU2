"""
El contexto Identidad reutiliza los enumerados transversales de `shared`
(TipoPerfil, EstadoValidacion). Se mantiene el modulo como punto unico de
importacion por si aparecen enumerados propios del contexto.
"""
from apps.shared.domain.enums import EstadoValidacion, TipoPerfil

__all__ = ["EstadoValidacion", "TipoPerfil"]
