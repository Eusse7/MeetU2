# reservas/domain/reserva_builder.py
from reservas.models import Reserva, Experiencia
from decimal import Decimal

class ReservaBuilderError(Exception):
    pass

class ReservaBuilder:
    def __init__(self):
        self._usuario = None
        self._experiencia = None
        self._cantidad_cupos = 1

    def para_usuario(self, usuario):
        self._usuario = usuario
        return self  

    def para_experiencia(self, experiencia: Experiencia):
        self._experiencia = experiencia
        return self

    def con_cupos(self, cantidad: int):
        if cantidad < 1:
            raise ReservaBuilderError("La cantidad de cupos debe ser al menos 1")
        self._cantidad_cupos = cantidad
        return self

    def _validar(self):
        if not self._usuario:
            raise ReservaBuilderError("Falta el usuario")
        if not self._experiencia:
            raise ReservaBuilderError("Falta la experiencia")
        if self._experiencia.estado == 'cancelada':
            raise ReservaBuilderError("La experiencia está cancelada")
        if self._experiencia.cupo_disponible < self._cantidad_cupos:
            raise ReservaBuilderError("No hay cupo suficiente")
        
    def _calcular_precio(self):
        precio_base = self._experiencia.precio * self._cantidad_cupos
        es_primera_reserva = not Reserva.objects.filter(usuario=self._usuario).exists()
        if es_primera_reserva:
            precio_base *= Decimal('0.9')  # antes: 0.9 (float) — corregido a Decimal
        return precio_base

    def build(self) -> Reserva:
        self._validar()
        precio_final = self._calcular_precio()

        reserva = Reserva.objects.create(
            usuario=self._usuario,
            experiencia=self._experiencia,
            cantidad_cupos=self._cantidad_cupos,
            precio_final=precio_final,
            estado='pendiente'
        )

        self._experiencia.cupo_disponible -= self._cantidad_cupos
        self._experiencia.save()

        return reserva