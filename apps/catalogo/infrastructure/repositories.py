"""
Adaptadores de persistencia: la unica parte del Catalogo que conoce el ORM.

Implementan los puertos de `application/ports.py`, de modo que los servicios
podrian correr contra Mongo, contra una API remota o contra dobles de prueba
sin cambiar una linea.
"""
from uuid import UUID

from django.db.models import F, Q

from apps.catalogo.application.dtos import FiltroExperienciasDTO
from apps.catalogo.application.ports import (
    CategoriaRepositoryPort,
    ExperienciaRepositoryPort,
    UbicacionRepositoryPort,
)
from apps.catalogo.domain.enums import EstadoExperiencia
from apps.catalogo.domain.models import CategoriaInteres, Experiencia, Ubicacion


class DjangoExperienciaRepository(ExperienciaRepositoryPort):
    def _base_queryset(self):
        return Experiencia.objects.select_related("ubicacion").prefetch_related(
            "categorias"
        )

    def guardar(self, experiencia: Experiencia) -> Experiencia:
        experiencia.full_clean(exclude=["id"], validate_constraints=False)
        experiencia.save()
        return experiencia

    def obtener_por_id(self, id_experiencia: UUID) -> Experiencia | None:
        return self._base_queryset().filter(pk=id_experiencia).first()

    def buscar(self, filtro: FiltroExperienciasDTO) -> list[Experiencia]:
        qs = self._base_queryset().filter(
            estado__in=[EstadoExperiencia.PUBLICADA, EstadoExperiencia.AGOTADA]
        )

        if filtro.texto:
            qs = qs.filter(
                Q(titulo__icontains=filtro.texto)
                | Q(descripcion__icontains=filtro.texto)
            )
        if filtro.ciudad:
            qs = qs.filter(ubicacion__ciudad__iexact=filtro.ciudad)
        if filtro.categorias:
            qs = qs.filter(categorias__id__in=list(filtro.categorias)).distinct()
        if filtro.fecha_desde:
            qs = qs.filter(fecha_hora__gte=filtro.fecha_desde)
        if filtro.fecha_hasta:
            qs = qs.filter(fecha_hora__lte=filtro.fecha_hasta)
        if filtro.precio_maximo is not None:
            qs = qs.filter(precio__lte=filtro.precio_maximo)
        if filtro.solo_con_cupo:
            qs = qs.filter(cupo_disponible__gt=0, estado=EstadoExperiencia.PUBLICADA)

        return list(qs)

    def listar_por_organizador(self, id_organizador: UUID) -> list[Experiencia]:
        return list(
            self._base_queryset()
            .filter(organizador_id=id_organizador)
            .order_by("-creado_en")
        )

    def asignar_categorias(
        self, experiencia: Experiencia, categorias: list[CategoriaInteres]
    ) -> None:
        experiencia.categorias.set(categorias)

    def descontar_cupo(self, id_experiencia: UUID, cantidad: int) -> bool:
        """
        UPDATE condicional en una sola sentencia SQL.

        La condicion `cupo_disponible__gte=cantidad` viaja al WHERE, asi que la
        base de datos resuelve la carrera: si dos peticiones concurrentes piden
        el ultimo cupo, solo una afecta filas y la otra recibe False.
        """
        filas = Experiencia.objects.filter(
            pk=id_experiencia,
            cupo_disponible__gte=cantidad,
        ).update(cupo_disponible=F("cupo_disponible") - cantidad)
        return filas == 1

    def reponer_cupo(self, id_experiencia: UUID, cantidad: int) -> None:
        Experiencia.objects.filter(
            pk=id_experiencia,
            cupo_disponible__lte=F("cupo_maximo") - cantidad,
        ).update(cupo_disponible=F("cupo_disponible") + cantidad)


class DjangoUbicacionRepository(UbicacionRepositoryPort):
    def guardar(self, ubicacion: Ubicacion) -> Ubicacion:
        ubicacion.full_clean(exclude=["id"])
        ubicacion.save()
        return ubicacion

    def obtener_por_id(self, id_ubicacion: UUID) -> Ubicacion | None:
        return Ubicacion.objects.filter(pk=id_ubicacion).first()

    def listar(self) -> list[Ubicacion]:
        return list(Ubicacion.objects.all())


class DjangoCategoriaRepository(CategoriaRepositoryPort):
    def guardar(self, categoria: CategoriaInteres) -> CategoriaInteres:
        categoria.full_clean(exclude=["id", "slug"])
        categoria.save()
        return categoria

    def listar_activas(self) -> list[CategoriaInteres]:
        return list(CategoriaInteres.objects.filter(activa=True))

    def obtener_muchas(self, ids: list[UUID]) -> list[CategoriaInteres]:
        return list(CategoriaInteres.objects.filter(id__in=ids, activa=True))
