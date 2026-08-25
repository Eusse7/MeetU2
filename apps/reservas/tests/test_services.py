"""
Pruebas de la capa de aplicacion de Reservas.

Ejercitan el flujo transaccional completo sin base de datos, sin HTTP y sin
enviar notificaciones: los servicios reciben dobles a traves de sus puertos.
"""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.catalogo.domain.exceptions import CupoInsuficiente
from apps.reservas.application.dtos import (
    CancelarReservaDTO,
    CheckInDTO,
    ConfirmarReservaDTO,
    SolicitarReservaDTO,
)
from apps.reservas.application.ports import ExperienciaVista, UsuarioVista
from apps.reservas.application.services import (
    CancelarReservaService,
    ConfirmarReservaService,
    ListarReservasUsuarioService,
    RegistrarCheckInService,
    SolicitarReservaService,
)
from apps.reservas.domain.enums import EstadoReserva
from apps.reservas.domain.exceptions import (
    ReservaDuplicada,
    ReservaExpirada,
    UsuarioNoAutorizado,
)
from apps.shared.tests.dobles import (
    CatalogoFalso,
    NotificadorEspia,
    PerfilFalso,
    ReservaRepositoryEnMemoria,
)

AHORA = timezone.now()
ID_USUARIO = uuid4()
ID_ORGANIZADOR = uuid4()


def experiencia_vista(**cambios) -> ExperienciaVista:
    datos = {
        "id": uuid4(),
        "titulo": "Cata de cafes de origen",
        "organizador_id": ID_ORGANIZADOR,
        "fecha_hora": AHORA + timedelta(days=5),
        "precio": Decimal("45000"),
        "cupo_disponible": 10,
        "estado": "PUBLICADA",
        "ciudad": "Medellin",
        "direccion": "Cra 35",
    }
    datos.update(cambios)
    return ExperienciaVista(**datos)


def usuario_vista(activo: bool = True) -> UsuarioVista:
    return UsuarioVista(
        id=ID_USUARIO, nombre="Andres", correo="andres@meetu2.co", activo=activo
    )


def armar_solicitud(experiencia=None, reservas=None, usuario=None, **kwargs):
    """Compone el servicio con dobles. Es la misma forma que usa el container."""
    catalogo = CatalogoFalso(experiencia=experiencia or experiencia_vista())
    repo = reservas if reservas is not None else ReservaRepositoryEnMemoria()
    notificador = NotificadorEspia()
    servicio = SolicitarReservaService(
        reservas=repo,
        catalogo=catalogo,
        perfiles=PerfilFalso(usuario or usuario_vista()),
        notificador=notificador,
        comision=kwargs.get("comision", Decimal("0.10")),
        minutos_expiracion=kwargs.get("minutos_expiracion", 30),
        max_cupos_por_reserva=kwargs.get("max_cupos", 5),
        reloj=lambda: AHORA,
    )
    return servicio, catalogo, repo, notificador


# ------------------------------------------------------- Solicitar reserva
def test_solicitar_reserva_congela_precio_y_calcula_comision():
    experiencia = experiencia_vista()
    servicio, catalogo, _, notificador = armar_solicitud(experiencia)

    reserva = servicio.ejecutar(
        SolicitarReservaDTO(
            id_usuario=ID_USUARIO, id_experiencia=experiencia.id, cantidad_cupos=2
        )
    )

    assert reserva.estado == EstadoReserva.PENDIENTE_PAGO
    assert reserva.precio_unitario == Decimal("45000")
    assert reserva.monto_total == Decimal("90000.00")
    assert reserva.comision_plataforma == Decimal("9000.00")
    assert reserva.codigo_ticket
    assert notificador.eventos == ["reserva_creada"]


def test_solicitar_reserva_bloquea_el_cupo_en_catalogo():
    experiencia = experiencia_vista()
    servicio, catalogo, _, _ = armar_solicitud(experiencia)

    servicio.ejecutar(
        SolicitarReservaDTO(
            id_usuario=ID_USUARIO, id_experiencia=experiencia.id, cantidad_cupos=3
        )
    )

    assert catalogo.bloqueos == [3]


def test_la_reserva_nace_con_ventana_de_pago():
    experiencia = experiencia_vista()
    servicio, _, _, _ = armar_solicitud(experiencia, minutos_expiracion=45)

    reserva = servicio.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    assert reserva.vence_en == AHORA + timedelta(minutes=45)


def test_no_se_puede_reservar_dos_veces_la_misma_experiencia():
    experiencia = experiencia_vista()
    servicio, _, _, _ = armar_solicitud(experiencia)
    dto = SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    servicio.ejecutar(dto)

    with pytest.raises(ReservaDuplicada) as exc:
        servicio.ejecutar(dto)

    assert exc.value.status_code == 409


def test_si_catalogo_rechaza_el_cupo_no_queda_reserva():
    experiencia = experiencia_vista()
    servicio, catalogo, repo, notificador = armar_solicitud(experiencia)
    catalogo.error_al_bloquear = CupoInsuficiente("Quedan 0 cupos")

    with pytest.raises(CupoInsuficiente):
        servicio.ejecutar(
            SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
        )

    assert repo.items == []
    assert notificador.eventos == []


def test_usuario_inactivo_no_puede_reservar():
    experiencia = experiencia_vista()
    servicio, _, _, _ = armar_solicitud(experiencia, usuario=usuario_vista(activo=False))

    with pytest.raises(UsuarioNoAutorizado):
        servicio.ejecutar(
            SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
        )


def test_no_se_reserva_una_experiencia_que_ya_ocurrio():
    experiencia = experiencia_vista(fecha_hora=AHORA - timedelta(hours=1))
    servicio, _, _, _ = armar_solicitud(experiencia)

    with pytest.raises(Exception) as exc:
        servicio.ejecutar(
            SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
        )

    assert "ya ocurrio" in str(exc.value)


# ------------------------------------------------------- Confirmar reserva
def test_confirmar_limpia_el_vencimiento_y_notifica():
    experiencia = experiencia_vista()
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    confirmada = ConfirmarReservaService(
        reservas=repo,
        catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()),
        notificador=notificador,
        reloj=lambda: AHORA + timedelta(minutes=5),
    ).ejecutar(ConfirmarReservaDTO(id_reserva=reserva.id, referencia_pago="TX-1"))

    assert confirmada.estado == EstadoReserva.CONFIRMADA
    assert confirmada.vence_en is None
    assert notificador.eventos == ["reserva_creada", "reserva_confirmada"]


def test_confirmar_fuera_de_la_ventana_de_pago_es_409():
    experiencia = experiencia_vista()
    solicitar, catalogo, repo, notificador = armar_solicitud(
        experiencia, minutos_expiracion=30
    )
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    with pytest.raises(ReservaExpirada) as exc:
        ConfirmarReservaService(
            reservas=repo,
            catalogo=catalogo,
            perfiles=PerfilFalso(usuario_vista()),
            notificador=notificador,
            reloj=lambda: AHORA + timedelta(hours=2),
        ).ejecutar(ConfirmarReservaDTO(id_reserva=reserva.id))

    assert exc.value.status_code == 409


# -------------------------------------------------------- Cancelar reserva
def test_cancelar_devuelve_el_cupo_al_catalogo():
    experiencia = experiencia_vista()
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(
            id_usuario=ID_USUARIO, id_experiencia=experiencia.id, cantidad_cupos=2
        )
    )

    CancelarReservaService(
        reservas=repo,
        catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()),
        notificador=notificador,
        reloj=lambda: AHORA,
    ).ejecutar(CancelarReservaDTO(id_reserva=reserva.id, id_usuario=ID_USUARIO))

    assert catalogo.liberaciones == [2]
    assert catalogo.cupo_disponible == 10


def test_cancelar_con_mas_de_48h_reembolsa_todo_lo_pagado():
    experiencia = experiencia_vista(fecha_hora=AHORA + timedelta(days=10))
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )
    ConfirmarReservaService(
        reservas=repo, catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()), notificador=notificador,
        reloj=lambda: AHORA,
    ).ejecutar(ConfirmarReservaDTO(id_reserva=reserva.id))

    resultado = CancelarReservaService(
        reservas=repo, catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()), notificador=notificador,
        reloj=lambda: AHORA,
    ).ejecutar(CancelarReservaDTO(id_reserva=reserva.id, id_usuario=ID_USUARIO))

    assert resultado.porcentaje_aplicado == Decimal("1.00")
    assert resultado.monto_reembolsado == Decimal("45000.00")


def test_cancelar_sin_haber_pagado_no_genera_reembolso():
    experiencia = experiencia_vista(fecha_hora=AHORA + timedelta(days=10))
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    resultado = CancelarReservaService(
        reservas=repo, catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()), notificador=notificador,
        reloj=lambda: AHORA,
    ).ejecutar(CancelarReservaDTO(id_reserva=reserva.id, id_usuario=ID_USUARIO))

    assert resultado.monto_reembolsado == Decimal("0.00")


def test_solo_el_titular_puede_cancelar():
    experiencia = experiencia_vista()
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    with pytest.raises(UsuarioNoAutorizado):
        CancelarReservaService(
            reservas=repo, catalogo=catalogo,
            perfiles=PerfilFalso(usuario_vista()), notificador=notificador,
            reloj=lambda: AHORA,
        ).ejecutar(CancelarReservaDTO(id_reserva=reserva.id, id_usuario=uuid4()))


# ---------------------------------------------------------------- Check-in
def test_check_in_marca_la_asistencia_dentro_de_la_ventana():
    experiencia = experiencia_vista(fecha_hora=AHORA + timedelta(hours=1))
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )
    ConfirmarReservaService(
        reservas=repo, catalogo=catalogo,
        perfiles=PerfilFalso(usuario_vista()), notificador=notificador,
        reloj=lambda: AHORA,
    ).ejecutar(ConfirmarReservaDTO(id_reserva=reserva.id))

    resultado = RegistrarCheckInService(
        reservas=repo, catalogo=catalogo, horas_ventana=3, reloj=lambda: AHORA
    ).ejecutar(
        CheckInDTO(codigo_ticket=reserva.codigo_ticket, id_organizador=ID_ORGANIZADOR)
    )

    assert resultado.estado == EstadoReserva.CHECK_IN
    assert resultado.check_in_en == AHORA


def test_otro_organizador_no_puede_validar_el_ticket():
    experiencia = experiencia_vista(fecha_hora=AHORA + timedelta(hours=1))
    solicitar, catalogo, repo, notificador = armar_solicitud(experiencia)
    reserva = solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    with pytest.raises(UsuarioNoAutorizado):
        RegistrarCheckInService(
            reservas=repo, catalogo=catalogo, horas_ventana=3, reloj=lambda: AHORA
        ).ejecutar(
            CheckInDTO(codigo_ticket=reserva.codigo_ticket, id_organizador=uuid4())
        )


# ------------------------------------------------------------- Composicion
def test_mis_reservas_compone_datos_de_dos_contextos():
    experiencia = experiencia_vista()
    solicitar, catalogo, repo, _ = armar_solicitud(experiencia)
    solicitar.ejecutar(
        SolicitarReservaDTO(id_usuario=ID_USUARIO, id_experiencia=experiencia.id)
    )

    detalladas = ListarReservasUsuarioService(
        reservas=repo, catalogo=catalogo
    ).ejecutar(ID_USUARIO)

    assert len(detalladas) == 1
    assert detalladas[0].experiencia_titulo == "Cata de cafes de origen"
    assert detalladas[0].experiencia_ciudad == "Medellin"
