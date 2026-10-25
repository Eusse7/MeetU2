"""
Casos de uso del contexto Social.

Orquestan la publicacion de calificaciones, validando que el usuario tenga
asistencia confirmada (check-in) en la reserva indicada, y recalculando
la calificacion promedio del organizador.
"""
from uuid import UUID

from apps.shared.application.unit_of_work import SinTransaccion, UnitOfWorkPort
from apps.social.application.dtos import (
    CrearResenaDTO,
    MetricasExperienciaDTO,
    MetricasOrganizadorDTO,
)
from apps.social.application.ports import (
    OrganizadorCalificacionPort,
    ResenaRepositoryPort,
    ReservaAsistenciaPort,
)
from apps.social.domain.exceptions import (
    ResenaDuplicada,
    ResenaNoEncontrada,
    ReservaNoEncontrada,
)
from apps.social.domain.models import Resena
from apps.social.domain.policies import CalculadoraPromedio, PoliticaResena


class CrearResenaService:
    """Publica una reseña tras verificar la asistencia por check-in."""

    def __init__(
        self,
        resenas: ResenaRepositoryPort,
        asistencia: ReservaAsistenciaPort,
        calificaciones_organizador: OrganizadorCalificacionPort,
        uow: UnitOfWorkPort | None = None,
    ):
        self._resenas = resenas
        self._asistencia = asistencia
        self._calificaciones_organizador = calificaciones_organizador
        self._uow = uow or SinTransaccion()

    def ejecutar(self, dto: CrearResenaDTO) -> Resena:
        PoliticaResena.validar_calificacion(dto.calificacion)

        existente = self._resenas.obtener_por_reserva(dto.id_reserva)
        if existente is not None:
            raise ResenaDuplicada("Ya existe una reseña para esta reserva")

        reserva = self._asistencia.obtener_asistencia(dto.id_reserva)
        if reserva is None:
            raise ReservaNoEncontrada(f"No existe la reserva {dto.id_reserva}")

        PoliticaResena.validar_asistencia(
            id_usuario=dto.id_usuario,
            reserva_usuario_id=reserva.usuario_id,
            reserva_estado=reserva.estado,
            tiene_check_in=reserva.check_in_en is not None,
        )

        resena = Resena(
            reserva_id=reserva.id,
            usuario_id=dto.id_usuario,
            experiencia_id=reserva.experiencia_id,
            organizador_id=reserva.organizador_id,
            calificacion=dto.calificacion,
            comentario=dto.comentario.strip(),
        )

        with self._uow:
            guardada = self._resenas.guardar(resena)
            calificaciones = self._resenas.obtener_calificaciones_organizador(
                reserva.organizador_id
            )
            nuevo_promedio = CalculadoraPromedio.calcular(calificaciones)
            self._calificaciones_organizador.actualizar_calificacion_promedio(
                reserva.organizador_id, nuevo_promedio
            )

        return guardada


class ObtenerResenaService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_resena: UUID) -> Resena:
        resena = self._resenas.obtener_por_id(id_resena)
        if resena is None:
            raise ResenaNoEncontrada(f"No existe la reseña {id_resena}")
        return resena


class ObtenerResenaDeReservaService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_reserva: UUID) -> Resena | None:
        return self._resenas.obtener_por_reserva(id_reserva)


class ListarResenasExperienciaService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_experiencia: UUID) -> list[Resena]:
        return self._resenas.listar_por_experiencia(id_experiencia)


class ListarResenasOrganizadorService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_organizador: UUID) -> list[Resena]:
        return self._resenas.listar_por_organizador(id_organizador)


class ListarResenasUsuarioService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_usuario: UUID) -> list[Resena]:
        return self._resenas.listar_por_usuario(id_usuario)


class ListarResenasRecientesService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, limite: int = 20) -> list[Resena]:
        return self._resenas.listar_recientes(limite)


class ObtenerMetricasOrganizadorService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_organizador: UUID) -> MetricasOrganizadorDTO:
        calificaciones = self._resenas.obtener_calificaciones_organizador(id_organizador)
        promedio = CalculadoraPromedio.calcular(calificaciones)
        desglose = {i: calificaciones.count(i) for i in range(1, 6)}
        return MetricasOrganizadorDTO(
            id_organizador=id_organizador,
            calificacion_promedio=promedio,
            total_resenas=len(calificaciones),
            desglose=desglose,
        )


class ObtenerMetricasExperienciaService:
    def __init__(self, resenas: ResenaRepositoryPort):
        self._resenas = resenas

    def ejecutar(self, id_experiencia: UUID) -> MetricasExperienciaDTO:
        calificaciones = self._resenas.obtener_calificaciones_experiencia(id_experiencia)
        promedio = CalculadoraPromedio.calcular(calificaciones)
        desglose = {i: calificaciones.count(i) for i in range(1, 6)}
        return MetricasExperienciaDTO(
            id_experiencia=id_experiencia,
            calificacion_promedio=promedio,
            total_resenas=len(calificaciones),
            desglose=desglose,
        )
