# reservas/services.py
from reservas.domain.reserva_builder import ReservaBuilder, ReservaBuilderError
from reservas.infra.notificador_factory import NotificadorFactory
from reservas.models import Experiencia

class ReservaService:
    def __init__(self, notificador=None):
        self.notificador = notificador or NotificadorFactory.crear()

    def crear_reserva(self, usuario, experiencia_id, cantidad_cupos=1):
        experiencia = Experiencia.objects.get(id=experiencia_id)

        reserva = (
            ReservaBuilder()
            .para_usuario(usuario)
            .para_experiencia(experiencia)
            .con_cupos(cantidad_cupos)
            .build()
        )

        self.notificador.enviar_confirmacion(reserva)
        return reserva