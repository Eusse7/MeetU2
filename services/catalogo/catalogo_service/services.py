"""Servicio de aplicacion del microservicio Catalogo."""
from datetime import datetime
from typing import List, Optional
import uuid

from catalogo_service.domain import Categoria, EstadoExperiencia, Experiencia, Modalidad, Ubicacion
from catalogo_service.errors import CupoExcedeAforoError, ExperienciaNoEncontradaError, UbicacionNoEncontradaError
from catalogo_service.repository import SQLAlchemyCatalogoRepository


class CatalogoService:
    def __init__(self, repository: SQLAlchemyCatalogoRepository):
        self.repository = repository

    def crear_categoria(self, nombre: str, descripcion: str = "") -> Categoria:
        categoria = Categoria(nombre=nombre, descripcion=descripcion)
        return self.repository.guardar_categoria(categoria)

    def listar_categorias(self) -> List[Categoria]:
        return self.repository.listar_categorias()

    def crear_ubicacion(
        self,
        nombre: str,
        direccion: str,
        ciudad: str,
        latitud: float,
        longitud: float,
        aforo_maximo: int,
    ) -> Ubicacion:
        ubicacion = Ubicacion(
            nombre=nombre,
            direccion=direccion,
            ciudad=ciudad,
            latitud=latitud,
            longitud=longitud,
            aforo_maximo=aforo_maximo,
        )
        return self.repository.guardar_ubicacion(ubicacion)

    def listar_ubicaciones(self) -> List[Ubicacion]:
        return self.repository.listar_ubicaciones()

    def crear_experiencia(
        self,
        organizador_id: uuid.UUID,
        categoria_id: uuid.UUID,
        ubicacion_id: uuid.UUID,
        titulo: str,
        descripcion: str,
        precio_cop: float,
        cupo_maximo: int,
        fecha_evento: datetime,
        modalidad: Modalidad = Modalidad.PRESENCIAL,
    ) -> Experiencia:
        ubicacion = self.repository.obtener_ubicacion(ubicacion_id)
        if not ubicacion:
            raise UbicacionNoEncontradaError(str(ubicacion_id))

        if cupo_maximo > ubicacion.aforo_maximo:
            raise CupoExcedeAforoError(cupo_maximo, ubicacion.aforo_maximo)

        exp = Experiencia(
            organizador_id=organizador_id,
            categoria_id=categoria_id,
            ubicacion_id=ubicacion_id,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            precio_cop=float(precio_cop),
            cupo_maximo=cupo_maximo,
            cupos_disponibles=cupo_maximo,
            fecha_evento=fecha_evento,
            modalidad=modalidad,
            estado=EstadoExperiencia.PUBLICADA,
        )
        return self.repository.guardar_experiencia(exp)

    def listar_experiencias(
        self,
        categoria_id: Optional[uuid.UUID] = None,
        precio_max: Optional[float] = None,
    ) -> List[Experiencia]:
        return self.repository.listar_experiencias(categoria_id=categoria_id, precio_max=precio_max)

    def obtener_experiencia(self, exp_id: uuid.UUID) -> Experiencia:
        exp = self.repository.obtener_experiencia(exp_id)
        if not exp:
            raise ExperienciaNoEncontradaError(str(exp_id))
        return exp
