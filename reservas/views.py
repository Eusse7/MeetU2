from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from reservas.services import ReservaService
from reservas.domain.reserva_builder import ReservaBuilderError

@method_decorator(login_required, name='dispatch')
class CrearReservaView(View):
    def get(self, request):
        return render(request, 'reservas/crear_reserva.html')

    def post(self, request):
        try:
            service = ReservaService()
            reserva = service.crear_reserva(
                usuario=request.user,
                experiencia_id=request.POST['experiencia_id'],
                cantidad_cupos=int(request.POST.get('cantidad_cupos', 1))
            )
            return JsonResponse({'reserva_id': reserva.id, 'precio_final': str(reserva.precio_final)})
        except ReservaBuilderError as e:
            return JsonResponse({'error': str(e)}, status=400)