"""
Libera el cupo de las reservas que vencieron sin pago.

En produccion esto seria un job periodico (Celery beat / cron). Se expone como
comando para que la logica viva en el servicio y no en el planificador: cambiar
de mecanismo de disparo no toca la capa de aplicacion.

    python manage.py expirar_reservas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.reservas import container
from apps.reservas.infrastructure.repositories import DjangoReservaRepository


class Command(BaseCommand):
    help = "Marca como EXPIRADAS las reservas pendientes vencidas y devuelve su cupo."

    def handle(self, *args, **opciones):
        pendientes = DjangoReservaRepository().listar_pendientes_vencidas(
            timezone.now()
        )
        expiradas = container.expirar_reservas_vencidas().ejecutar(pendientes)

        self.stdout.write(
            self.style.SUCCESS(f"Reservas expiradas y cupos liberados: {expiradas}")
        )
