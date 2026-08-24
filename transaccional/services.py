from transaccional.domain.reserva_builder import ReservaBuilder
from transaccional.infra.notificador_factory import NotificadorFactory
from django.core.exceptions import ValidationError
from django.db import transaction

class ReservasService:
    @staticmethod
    def procesar_reserva(datos_reserva):
        try:
            with transaction.atomic():
                builder = ReservaBuilder()
                reserva = (builder
                           .con_experiencia(datos_reserva['experiencia_id'])
                           .para_personas(datos_reserva['cantidad_personas'])
                           .calcular_monto()
                           .build())
                
                notificador = NotificadorFactory.obtener_procesador()
                notificador.procesar(f"Confirmación para reserva {reserva.id} por {reserva.monto_total}")
                
                return reserva, None
                
        except ValidationError as e:
            return None, str(e.message) if hasattr(e, 'message') else str(e.messages[0])
        except Exception as e:
            return None, "Error inesperado al procesar la reserva."