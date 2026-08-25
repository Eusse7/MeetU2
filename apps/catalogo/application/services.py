"""
Capa de aplicacion del Catalogo: un caso de uso, un servicio (SRP).

Cada servicio recibe sus dependencias por constructor (Inyeccion de
Dependencias sobre los puertos de `application/ports.py`), orquesta politicas
de dominio y repositorios, y no sabe nada de HTTP.
"""
from uuid import UUID

from django.utils import timezone

from apps.catalogo.application.builders import ExperienciaBuilder
from apps.catalogo.application.dtos import (
    CrearCategoriaDTO,
    CrearUbicacionDTO,
    ExperienciaRecomendadaDTO,
    FiltroExperienciasDTO,
    PublicarExperienciaDTO,
)
from apps.catalogo.application.ports import (
    CategoriaRepositoryPort,
    ExperienciaRepositoryPort,
    InteresesUsuarioPort,
    OrganizadorPort,
    UbicacionRepositoryPort,
)
from apps.catalogo.domain.enums import EstadoExperiencia
from apps.catalogo.domain.exceptions import (
    CategoriaNoEncontrada,
    CupoInsuficiente,
    ExperienciaNoDisponible,
    ExperienciaNoEncontrada,
    OrganizadorNoAutorizado,
    UbicacionNoEncontrada,
)
from apps.catalogo.domain.models import CategoriaInteres, Experiencia, Ubicacion
from apps.catalogo.domain.policies import (
    CicloVidaExperiencia,
    PoliticaAfinidad,
    PoliticaAforo,
)
from apps.shared.application.unit_of_work import SinTransaccion, UnitOfWorkPort


class CrearUbicacionService:
    """Alta de un sitio donde se pueden realizar experiencias."""

    def __init__(self, ubicaciones: UbicacionRepositoryPort):
        self._ubicaciones = ubicaciones

    def ejecutar(self, dto: CrearUbicacionDTO) -> Ubicacion:
        ubicacion = Ubicacion(
            nombre=dto.nombre.strip(),
            direccion=dto.direccion.strip(),
            ciudad=dto.ciudad.strip(),
            latitud=dto.latitud,
            longitud=dto.longitud,
            aforo_maximo=dto.aforo_maximo,
        )
        return self._ubicaciones.guardar(ubicacion)


class ListarUbicacionesService:
    def __init__(self, ubicaciones: UbicacionRepositoryPort):
        self._ubicaciones = ubicaciones

    def ejecutar(self) -> list[Ubicacion]:
        return self._ubicaciones.listar()


class CrearCategoriaService:
    def __init__(self, categorias: CategoriaRepositoryPort):
        self._categorias = categorias

    def ejecutar(self, dto: CrearCategoriaDTO) -> CategoriaInteres:
        categoria = CategoriaInteres(
            nombre=dto.nombre.strip(),
            descripcion=dto.descripcion.strip(),
        )
        return self._categorias.guardar(categoria)


class ListarCategoriasService:
    def __init__(self, categorias: CategoriaRepositoryPort):
        self._categorias = categorias

    def ejecutar(self) -> list[CategoriaInteres]:
        return self._categorias.listar_activas()


class PublicarExperienciaService:
    """
    Caso de uso: un organizador verificado publica una experiencia.

    Responsabilidad unica: autorizar, delegar el armado en el Builder y
    persistir de forma atomica junto con sus categorias.
    """

    def __init__(
        self,
        experiencias: ExperienciaRepositoryPort,
        ubicaciones: UbicacionRepositoryPort,
        categorias: CategoriaRepositoryPort,
        organizadores: OrganizadorPort,
        uow: UnitOfWorkPort | None = None,
        reloj=timezone.now,
    ):
        self._experiencias = experiencias
        self._ubicaciones = ubicaciones
        self._categorias = categorias
        self._organizadores = organizadores
        self._uow = uow or SinTransaccion()
        self._reloj = reloj

    def ejecutar(self, dto: PublicarExperienciaDTO) -> Experiencia:
        if not self._organizadores.existe(dto.id_organizador):
            raise OrganizadorNoAutorizado(
                f"No existe el organizador {dto.id_organizador}"
            )
        if not self._organizadores.esta_verificado(dto.id_organizador):
            raise OrganizadorNoAutorizado(
                "El organizador debe estar VERIFICADO para publicar experiencias"
            )

        ubicacion = self._ubicaciones.obtener_por_id(dto.id_ubicacion)
        if ubicacion is None:
            raise UbicacionNoEncontrada(f"No existe la ubicacion {dto.id_ubicacion}")

        categorias = self._resolver_categorias(dto.categorias)

        builder = (
            ExperienciaBuilder(ahora=self._reloj())
            .para_organizador(dto.id_organizador)
            .con_titulo(dto.titulo, dto.descripcion)
            .en_ubicacion(ubicacion)
            .en_fecha(dto.fecha_hora, dto.duracion_minutos)
            .con_precio(dto.precio, dto.descuento_porcentaje)
            .con_cupo(dto.cupo_maximo)
            .con_modalidad(dto.modalidad)
            .con_categorias(categorias)
        )
        if dto.publicar_de_inmediato:
            builder = builder.publicada()
        else:
            builder = builder.como_borrador()

        with self._uow:
            experiencia = self._experiencias.guardar(builder.construir())
            self._experiencias.asignar_categorias(experiencia, builder.categorias)

        return experiencia

    def _resolver_categorias(self, ids: tuple[UUID, ...]) -> list[CategoriaInteres]:
        if not ids:
            return []
        encontradas = self._categorias.obtener_muchas(list(ids))
        if len(encontradas) != len(set(ids)):
            raise CategoriaNoEncontrada(
                "Alguna de las categorias indicadas no existe o esta inactiva"
            )
        return encontradas


class BuscarExperienciasService:
    """Caso de uso Descubrir: catalogo publico filtrable."""

    def __init__(self, experiencias: ExperienciaRepositoryPort):
        self._experiencias = experiencias

    def ejecutar(self, filtro: FiltroExperienciasDTO) -> list[Experiencia]:
        return self._experiencias.buscar(filtro)


class ObtenerExperienciaService:
    def __init__(self, experiencias: ExperienciaRepositoryPort):
        self._experiencias = experiencias

    def ejecutar(self, id_experiencia: UUID) -> Experiencia:
        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if experiencia is None:
            raise ExperienciaNoEncontrada(f"No existe la experiencia {id_experiencia}")
        return experiencia


class ListarExperienciasOrganizadorService:
    def __init__(self, experiencias: ExperienciaRepositoryPort):
        self._experiencias = experiencias

    def ejecutar(self, id_organizador: UUID) -> list[Experiencia]:
        return self._experiencias.listar_por_organizador(id_organizador)


class RecomendarExperienciasService:
    """
    Materializa la propuesta de valor: ordenar el catalogo por afinidad con los
    intereses declarados del usuario.
    """

    def __init__(
        self,
        experiencias: ExperienciaRepositoryPort,
        intereses: InteresesUsuarioPort,
    ):
        self._experiencias = experiencias
        self._intereses = intereses

    def ejecutar(
        self, id_usuario: UUID, filtro: FiltroExperienciasDTO | None = None
    ) -> list[ExperienciaRecomendadaDTO]:
        perfil = self._intereses.obtener(id_usuario)
        candidatas = self._experiencias.buscar(filtro or FiltroExperienciasDTO())

        recomendadas: list[ExperienciaRecomendadaDTO] = []
        for experiencia in candidatas:
            categorias = {str(c.id): c.nombre for c in experiencia.categorias.all()}
            afinidad = PoliticaAfinidad.calcular_coincidencia(perfil, set(categorias))
            comunes = tuple(
                nombre for cid, nombre in categorias.items() if cid in perfil
            )
            recomendadas.append(
                ExperienciaRecomendadaDTO(
                    experiencia=experiencia,
                    afinidad=afinidad,
                    categorias_en_comun=comunes,
                )
            )

        recomendadas.sort(key=lambda r: (-r.afinidad, r.experiencia.fecha_hora))
        return recomendadas


class CancelarExperienciaService:
    """Un organizador retira su experiencia del catalogo."""

    def __init__(
        self,
        experiencias: ExperienciaRepositoryPort,
        organizadores: OrganizadorPort,
    ):
        self._experiencias = experiencias
        self._organizadores = organizadores

    def ejecutar(
        self, id_experiencia: UUID, id_organizador: UUID, motivo: str = ""
    ) -> Experiencia:
        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if experiencia is None:
            raise ExperienciaNoEncontrada(f"No existe la experiencia {id_experiencia}")
        if str(experiencia.organizador_id) != str(id_organizador):
            raise OrganizadorNoAutorizado(
                "Solo el organizador propietario puede cancelar la experiencia"
            )

        CicloVidaExperiencia.validar_transicion(
            experiencia.estado, EstadoExperiencia.CANCELADA
        )
        experiencia.estado = EstadoExperiencia.CANCELADA
        experiencia.motivo_cancelacion = (motivo or "").strip()[:255]
        return self._experiencias.guardar(experiencia)


class GestionCupoService:
    """
    Servicio de aforo. Es el unico punto del sistema autorizado a mover el
    `cupo_disponible`; el contexto Reservas lo consume a traves de un puerto.
    """

    def __init__(self, experiencias: ExperienciaRepositoryPort):
        self._experiencias = experiencias

    def bloquear(self, id_experiencia: UUID, cantidad: int) -> Experiencia:
        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if experiencia is None:
            raise ExperienciaNoEncontrada(f"No existe la experiencia {id_experiencia}")
        if not CicloVidaExperiencia.es_reservable(experiencia.estado):
            raise ExperienciaNoDisponible(
                f"La experiencia esta en estado {experiencia.estado} y no admite reservas"
            )
        if not PoliticaAforo.hay_disponibilidad(experiencia.cupo_disponible, cantidad):
            raise CupoInsuficiente(
                f"Quedan {experiencia.cupo_disponible} cupos y se solicitaron {cantidad}"
            )

        # Descuento atomico: evita la sobreventa cuando dos usuarios reservan el
        # ultimo cupo a la vez (la comprobacion previa solo mejora el mensaje).
        if not self._experiencias.descontar_cupo(id_experiencia, cantidad):
            raise CupoInsuficiente(
                "Otro usuario tomo el ultimo cupo mientras se procesaba la solicitud"
            )

        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if experiencia.cupo_disponible == 0:
            experiencia.estado = EstadoExperiencia.AGOTADA
            self._experiencias.guardar(experiencia)
        return experiencia

    def liberar(self, id_experiencia: UUID, cantidad: int) -> None:
        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if experiencia is None:
            raise ExperienciaNoEncontrada(f"No existe la experiencia {id_experiencia}")

        self._experiencias.reponer_cupo(id_experiencia, cantidad)

        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if (
            experiencia.estado == EstadoExperiencia.AGOTADA
            and experiencia.cupo_disponible > 0
        ):
            experiencia.estado = EstadoExperiencia.PUBLICADA
            self._experiencias.guardar(experiencia)
