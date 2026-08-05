import os

class NotificadorConsola:
    def enviar_confirmacion(self, reserva):
        print(f"[DEV] Confirmación enviada a {reserva.usuario.email} — Reserva #{reserva.id}")

class NotificadorEmailReal:
    def enviar_confirmacion(self, reserva):
        print(f"[PROD] Email real enviado a {reserva.usuario.email}")

class NotificadorFactory:
    @staticmethod
    def crear():
        env_type = os.getenv('ENV_TYPE', 'DEV')
        if env_type == 'PROD':
            return NotificadorEmailReal()
        return NotificadorConsola()