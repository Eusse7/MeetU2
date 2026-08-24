import os

class NotificadorMock:
    def procesar(self, mensaje):
        print(f"[MOCK PRUEBAS] Simulando notificación: {mensaje}")
        return True

class NotificadorReal:
    def procesar(self, mensaje):
        print(f"[PROCESADOR REAL] Ejecutando: {mensaje}")
        return True

class NotificadorFactory:
    @staticmethod
    def obtener_procesador():
        entorno = os.getenv('ENV_TYPE', 'DEV')
        if entorno == 'PROD':
            return NotificadorReal()
        return NotificadorMock()