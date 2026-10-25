"""
Pruebas unitarias de la capa de aplicacion del contexto Social.

Verifican las reglas de negocio con dobles de prueba en memoria,
sin base de datos y sin dependencias externas.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from apps.social.application.dtos import CrearResenaDTO
from apps.social.application.ports import ReservaAsistenciaVista
from apps.social.application.services import (
    CrearResenaService,
    ListarResenasExperienciaService,
    ListarResenasOrganizadorService,
    ListarResenasUsuarioService,
    ObtenerMetricasExperienciaService,
    ObtenerMetricasOrganizadorService,
    ObtenerResenaDeReservaService,
    ObtenerResenaService,
)
from apps.social.domain.exceptions import (
    CalificacionInvalida,
    ResenaDuplicada,
    ResenaNoEncontrada,
    ReservaNoEncontrada,
    ReservaNoPerteneceAUsuario,
    ReservaSinCheckIn,
)
from apps.social.tests.dobles import (
    OrganizadorCalificacionEspia,
    ResenaRepositoryEnMemoria,
    ReservaAsistenciaFalsa,
)


@pytest.fixture
def repo():
    return ResenaRepositoryEnMemoria()


@pytest.fixture
def asistencia():
    return ReservaAsistenciaFalsa()


@pytest.fixture
def espia_organizador():
    return OrganizadorCalificacionEspia()


@pytest.fixture
def servicio_crear(repo, asistencia, espia_organizador):
    return CrearResenaService(
        resenas=repo,
        asistencia=asistencia,
        calificaciones_organizador=espia_organizador,
    )


def test_crear_resena_exitoso(servicio_crear, repo, asistencia, espia_organizador):
    usuario_id = uuid4()
    exp_id = uuid4()
    org_id = uuid4()
    reserva_id = uuid4()

    asistencia.registrar(
        ReservaAsistenciaVista(
            id=reserva_id,
            usuario_id=usuario_id,
            experiencia_id=exp_id,
            organizador_id=org_id,
            estado="CHECK_IN",
            check_in_en=datetime.now(timezone.utc),
        )
    )

    dto = CrearResenaDTO(
        id_reserva=reserva_id,
        id_usuario=usuario_id,
        calificacion=5,
        comentario="Excelente experiencia, aprendi un monton.",
    )

    resena = servicio_crear.ejecutar(dto)

    assert resena.id is not None
    assert resena.reserva_id == reserva_id
    assert resena.usuario_id == usuario_id
    assert resena.experiencia_id == exp_id
    assert resena.organizador_id == org_id
    assert resena.calificacion == 5
    assert resena.comentario == "Excelente experiencia, aprendi un monton."
    assert espia_organizador.promedios[org_id] == Decimal("5.00")


def test_crear_resena_recalcula_promedio_organizador(servicio_crear, asistencia, espia_organizador):
    org_id = uuid4()
    exp_id = uuid4()

    # Usuario 1 deja calificacion 5
    u1, r1 = uuid4(), uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=r1, usuario_id=u1, experiencia_id=exp_id, organizador_id=org_id,
            estado="CHECK_IN", check_in_en=datetime.now(timezone.utc)
        )
    )
    servicio_crear.ejecutar(CrearResenaDTO(id_reserva=r1, id_usuario=u1, calificacion=5))
    assert espia_organizador.promedios[org_id] == Decimal("5.00")

    # Usuario 2 deja calificacion 3 -> promedio (5+3)/2 = 4.00
    u2, r2 = uuid4(), uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=r2, usuario_id=u2, experiencia_id=exp_id, organizador_id=org_id,
            estado="CHECK_IN", check_in_en=datetime.now(timezone.utc)
        )
    )
    servicio_crear.ejecutar(CrearResenaDTO(id_reserva=r2, id_usuario=u2, calificacion=3))
    assert espia_organizador.promedios[org_id] == Decimal("4.00")


def test_crear_resena_falla_si_reserva_no_existe(servicio_crear):
    with pytest.raises(ReservaNoEncontrada):
        servicio_crear.ejecutar(
            CrearResenaDTO(
                id_reserva=uuid4(),
                id_usuario=uuid4(),
                calificacion=5,
            )
        )


def test_crear_resena_falla_si_no_es_su_reserva(servicio_crear, asistencia):
    reserva_id = uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=reserva_id,
            usuario_id=uuid4(),
            experiencia_id=uuid4(),
            organizador_id=uuid4(),
            estado="CHECK_IN",
            check_in_en=datetime.now(timezone.utc),
        )
    )
    with pytest.raises(ReservaNoPerteneceAUsuario):
        servicio_crear.ejecutar(
            CrearResenaDTO(
                id_reserva=reserva_id,
                id_usuario=uuid4(),  # usuario distinto
                calificacion=5,
            )
        )


def test_crear_resena_falla_si_no_tiene_check_in(servicio_crear, asistencia):
    usuario_id = uuid4()
    reserva_id = uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=reserva_id,
            usuario_id=usuario_id,
            experiencia_id=uuid4(),
            organizador_id=uuid4(),
            estado="CONFIRMADA",  # no ha hecho check-in
            check_in_en=None,
        )
    )
    with pytest.raises(ReservaSinCheckIn):
        servicio_crear.ejecutar(
            CrearResenaDTO(
                id_reserva=reserva_id,
                id_usuario=usuario_id,
                calificacion=4,
            )
        )


def test_crear_resena_falla_si_ya_fue_calificada(servicio_crear, asistencia):
    usuario_id = uuid4()
    reserva_id = uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=reserva_id,
            usuario_id=usuario_id,
            experiencia_id=uuid4(),
            organizador_id=uuid4(),
            estado="CHECK_IN",
            check_in_en=datetime.now(timezone.utc),
        )
    )
    servicio_crear.ejecutar(
        CrearResenaDTO(id_reserva=reserva_id, id_usuario=usuario_id, calificacion=4)
    )

    with pytest.raises(ResenaDuplicada):
        servicio_crear.ejecutar(
            CrearResenaDTO(id_reserva=reserva_id, id_usuario=usuario_id, calificacion=5)
        )


def test_crear_resena_valida_rango_estrellas(servicio_crear):
    with pytest.raises(CalificacionInvalida):
        servicio_crear.ejecutar(
            CrearResenaDTO(id_reserva=uuid4(), id_usuario=uuid4(), calificacion=6)
        )


def test_obtener_resena(servicio_crear, repo, asistencia):
    u, r = uuid4(), uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=r, usuario_id=u, experiencia_id=uuid4(), organizador_id=uuid4(),
            estado="CHECK_IN", check_in_en=datetime.now(timezone.utc)
        )
    )
    creada = servicio_crear.ejecutar(CrearResenaDTO(id_reserva=r, id_usuario=u, calificacion=4))

    servicio_obtener = ObtenerResenaService(repo)
    encontrada = servicio_obtener.ejecutar(creada.id)
    assert encontrada.id == creada.id

    with pytest.raises(ResenaNoEncontrada):
        servicio_obtener.ejecutar(uuid4())


def test_obtener_resena_de_reserva(servicio_crear, repo, asistencia):
    u, r = uuid4(), uuid4()
    asistencia.registrar(
        ReservaAsistenciaVista(
            id=r, usuario_id=u, experiencia_id=uuid4(), organizador_id=uuid4(),
            estado="CHECK_IN", check_in_en=datetime.now(timezone.utc)
        )
    )
    servicio_obtener_reserva = ObtenerResenaDeReservaService(repo)
    assert servicio_obtener_reserva.ejecutar(r) is None

    creada = servicio_crear.ejecutar(CrearResenaDTO(id_reserva=r, id_usuario=u, calificacion=5))
    assert servicio_obtener_reserva.ejecutar(r).id == creada.id


def test_listar_y_metricas(servicio_crear, repo, asistencia):
    exp_id = uuid4()
    org_id = uuid4()

    for calif in [4, 5, 5]:
        u, r = uuid4(), uuid4()
        asistencia.registrar(
            ReservaAsistenciaVista(
                id=r, usuario_id=u, experiencia_id=exp_id, organizador_id=org_id,
                estado="CHECK_IN", check_in_en=datetime.now(timezone.utc)
            )
        )
        servicio_crear.ejecutar(CrearResenaDTO(id_reserva=r, id_usuario=u, calificacion=calif))

    resenas_exp = ListarResenasExperienciaService(repo).ejecutar(exp_id)
    assert len(resenas_exp) == 3

    resenas_org = ListarResenasOrganizadorService(repo).ejecutar(org_id)
    assert len(resenas_org) == 3

    metricas_exp = ObtenerMetricasExperienciaService(repo).ejecutar(exp_id)
    assert metricas_exp.total_resenas == 3
    # (4 + 5 + 5) / 3 = 4.67
    assert metricas_exp.calificacion_promedio == Decimal("4.67")
    assert metricas_exp.desglose[5] == 2
    assert metricas_exp.desglose[4] == 1
    assert metricas_exp.desglose[1] == 0

    metricas_org = ObtenerMetricasOrganizadorService(repo).ejecutar(org_id)
    assert metricas_org.total_resenas == 3
    assert metricas_org.calificacion_promedio == Decimal("4.67")
