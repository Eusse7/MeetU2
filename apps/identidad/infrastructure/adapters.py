"""
Capa anticorrupcion hacia el contexto Catalogo.

Identidad solo necesita comprobar que una categoria de interes existe. En vez
de importar el modelo en la capa de aplicacion, esa dependencia se expresa como
el puerto `CatalogoCategoriasPort` y se resuelve aqui.
"""
from uuid import UUID

from apps.catalogo.domain.models import CategoriaInteres
from apps.identidad.application.ports import CatalogoCategoriasPort


class CatalogoCategoriasAdapter(CatalogoCategoriasPort):
    def existe_categoria(self, id_categoria: UUID) -> bool:
        return CategoriaInteres.objects.filter(pk=id_categoria, activa=True).exists()
