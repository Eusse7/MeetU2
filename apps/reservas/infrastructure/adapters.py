"""
Adaptadores del contexto Reservas hacia el resto del sistema.

Implementan puertos declarados en `application/ports.py` y son la unica
frontera por la que Reservas toca Catalogo, Identidad, Notificaciones y el
microservicio de Pagos (este ultimo, por HTTP).
Traducen las entidades ajenas a las proyecciones propias (`ExperienciaVista`,
`UsuarioVista`), de modo que un cambio en otro contexto no se propaga.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from uuid import UUID

from apps.catalogo.application.services import GestionCupoService
from apps.catalogo.infrastructure.repositories import DjangoExperienciaRepository
from apps.identidad.domain.models import Usuario
from apps.notificaciones.application.ports import Notificacion
from apps.notificaciones.infrastructure.factories import NotificadorFactory
from apps.reservas.application.ports import (
    CatalogoPort,
    ExperienciaVista,
    NotificadorPort,
    PerfilUsuarioPort,
    UsuarioVista,
    VerificadorPagoPort,
)
from apps.reservas.domain.exceptions import PagoNoVerificado
from apps.reservas.domain.models import Reserva
from apps.shared.domain.exceptions import DomainError


class CatalogoServiceAdapter(CatalogoPort):
    """
    Habla con Catalogo a traves de su servicio de aplicacion, no de su ORM.

    Asi Catalogo conserva el control de sus invariantes de aforo: Reservas no
    puede restar cupo por su cuenta ni saltarse el estado de la experiencia.
    """

    def __init__(self, gestion_cupo: GestionCupoService | None = None):
        self._experiencias = DjangoExperienciaRepository()
        self._gestion_cupo = gestion_cupo or GestionCupoService(
            experiencias=self._experiencias
        )

    def obtener_experiencia(self, id_experiencia: UUID) -> ExperienciaVista | None:
        experiencia = self._experiencias.obtener_por_id(id_experiencia)
        if experiencia is None:
            return None
        return ExperienciaVista(
            id=experiencia.id,
            titulo=experiencia.titulo,
            organizador_id=experiencia.organizador_id,
            fecha_hora=experiencia.fecha_hora,
            precio=experiencia.precio,
            cupo_disponible=experiencia.cupo_disponible,
            estado=experiencia.estado,
            ciudad=experiencia.ubicacion.ciudad,
            direccion=experiencia.ubicacion.direccion,
        )

    def bloquear_cupo(self, id_experiencia: UUID, cantidad: int) -> None:
        self._gestion_cupo.bloquear(id_experiencia, cantidad)

    def liberar_cupo(self, id_experiencia: UUID, cantidad: int) -> None:
        self._gestion_cupo.liberar(id_experiencia, cantidad)


class IdentidadPerfilAdapter(PerfilUsuarioPort):
    def obtener(self, id_usuario: UUID) -> UsuarioVista | None:
        usuario = Usuario.objects.filter(pk=id_usuario).first()
        if usuario is None:
            return None
        return UsuarioVista(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            activo=usuario.activo,
        )


class NotificacionesAdapter(NotificadorPort):
    """
    Traduce eventos de negocio a mensajes y delega el envio en la Factory.

    Aqui se ve el patron completo: el servicio dice "reserva confirmada", este
    adaptador redacta el mensaje y `NotificadorFactory` decide por que canal
    sale segun la configuracion del entorno.
    """

    def __init__(self, canal: str | None = None):
        self._canal = canal

    def _enviar(self, destinatario: str, asunto: str, mensaje: str, **datos) -> None:
        NotificadorFactory.crear(self._canal).enviar(
            Notificacion(
                destinatario=destinatario,
                asunto=asunto,
                mensaje=mensaje,
                datos=datos,
            )
        )

    def reserva_creada(
        self,
        reserva: Reserva,
        usuario: UsuarioVista,
        experiencia: ExperienciaVista,
    ) -> None:
        self._enviar(
            usuario.correo,
            f"Reserva pendiente de pago - {experiencia.titulo}",
            (
                f"Hola {usuario.nombre}, apartamos {reserva.cantidad_cupos} cupo(s) "
                f"para '{experiencia.titulo}'.\n"
                f"Total a pagar: ${reserva.monto_total}\n"
                f"Ticket: {reserva.codigo_ticket}\n"
                f"Tienes hasta {reserva.vence_en:%d/%m/%Y %H:%M} para completar el pago."
            ),
            id_reserva=str(reserva.id),
            tipo="reserva_creada",
        )

    def reserva_confirmada(
        self,
        reserva: Reserva,
        usuario: UsuarioVista,
        experiencia: ExperienciaVista,
    ) -> None:
        self._enviar(
            usuario.correo,
            f"Reserva confirmada - {experiencia.titulo}",
            (
                f"Listo {usuario.nombre}, tu cupo esta confirmado.\n"
                f"Experiencia: {experiencia.titulo}\n"
                f"Cuando: {experiencia.fecha_hora:%d/%m/%Y %H:%M}\n"
                f"Donde: {experiencia.direccion} ({experiencia.ciudad})\n"
                f"Presenta este ticket en la entrada: {reserva.codigo_ticket}"
            ),
            id_reserva=str(reserva.id),
            tipo="reserva_confirmada",
        )

    def reserva_cancelada(
        self, reserva: Reserva, usuario: UsuarioVista, reembolso: Decimal
    ) -> None:
        detalle = (
            f"Se reembolsaran ${reembolso} segun la politica de cancelacion."
            if reembolso > 0
            else "Por la antelacion de la cancelacion no aplica reembolso."
        )
        self._enviar(
            usuario.correo,
            "Reserva cancelada",
            f"Hola {usuario.nombre}, cancelamos la reserva {reserva.codigo_ticket}.\n{detalle}",
            id_reserva=str(reserva.id),
            tipo="reserva_cancelada",
        )


class ServicioPagosNoDisponible(DomainError):
    codigo = "servicio_pagos_no_disponible"
    status_code = 503


class HttpVerificadorPago(VerificadorPagoPort):
    """
    Consulta al microservicio Flask de Pagos si una referencia es legitima.

    Es la costura del Strangler Pattern dentro del monolito: Reservas ya no
    sabe cobrar ni habla con pasarelas; solo pregunta por HTTP
    (GET /api/v2/pagos/referencias/<ref>) y valida la respuesta.
    """

    def __init__(self, url_base: str, timeout: float = 3.0):
        self._url = url_base.rstrip("/")
        self._timeout = timeout

    def verificar(self, referencia: str, id_reserva: UUID, monto: Decimal) -> None:
        pago = self._consultar(referencia)
        if pago.get("estado") != "APROBADO":
            raise PagoNoVerificado(
                f"El pago {referencia} esta en estado {pago.get('estado')}"
            )
        if str(pago.get("id_reserva")) != str(id_reserva):
            raise PagoNoVerificado(
                f"El pago {referencia} no corresponde a esta reserva"
            )
        if Decimal(str(pago.get("monto", "0"))) != Decimal(monto):
            raise PagoNoVerificado(
                f"El monto del pago {referencia} no coincide con el de la reserva"
            )

    def _consultar(self, referencia: str) -> dict:
        ruta = urllib.parse.quote(referencia, safe="")
        url = f"{self._url}/api/v2/pagos/referencias/{ruta}"
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as respuesta:
                return json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise PagoNoVerificado(
                    f"No existe un pago con referencia {referencia}"
                ) from exc
            raise ServicioPagosNoDisponible(
                f"El servicio de pagos respondio {exc.code}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise ServicioPagosNoDisponible(
                "El servicio de pagos no responde; intenta de nuevo"
            ) from exc
