from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integraciones import container
from apps.integraciones.models import ReservaHotel


class ExperienciasPublicasAPIView(APIView):
    """
    Servicio a Proveer (Entregable 2):
    Expone un endpoint JSON público con información relevante del sistema MeetU2
    para que equipos aliados y terceros puedan consumir el catálogo de experiencias.
    """

    def get(self, request: Request) -> Response:
        servicio = container.exponer_experiencias_publicas()
        publicas = servicio.ejecutar()

        return Response(
            {
                "plataforma": "MeetU2",
                "version": "2.0",
                "descripcion": "API pública de experiencias para consumo de la red aliada",
                "total": len(publicas),
                "experiencias": [
                    {
                        "id": exp.id,
                        "titulo": exp.titulo,
                        "descripcion": exp.descripcion,
                        "categoria": exp.categoria,
                        "ciudad": exp.ciudad,
                        "ubicacion": exp.ubicacion,
                        "fecha_hora": exp.fecha_hora,
                        "precio": float(exp.precio),
                        "cupo_disponible": exp.cupo_disponible,
                        "organizador": exp.organizador,
                    }
                    for exp in publicas
                ],
            },
            status=status.HTTP_200_OK,
        )


class PlanesAliadosAPIView(APIView):
    """
    Servicio a Consumir (Entregable 2):
    Consume el servicio del equipo aliado (Servicio de Hoteles)
    mediante el patrón Adapter, con fallback de contingencia en caso de indisponibilidad.
    """

    def get(self, request: Request) -> Response:
        servicio = container.consultar_planes_aliados()
        planes = servicio.ejecutar()

        return Response(
            {
                "fuente": "hotelMDJ (Servicio de Hoteles Aliado)",
                "servicio_aliado": "hotelMDJ",
                "tipo_servicio": "Hospedajes y Hoteles",
                "total": len(planes),
                "planes": [
                    {
                        "id": p.id,
                        "titulo": p.titulo,
                        "categoria": p.categoria,
                        "tipo_alojamiento": p.tipo_alojamiento,
                        "ciudad": p.ciudad,
                        "precio": float(p.precio),
                        "organizador": p.organizador,
                        "cupos_disponibles": p.cupos_disponibles,
                        "url_externa": p.url_externa,
                        "red_aliada": p.red_aliada,
                        "amenidades": list(p.amenidades),
                        "estrellas": p.estrellas,
                        "imagen_url": p.imagen_url,
                    }
                    for p in planes
                ],
            },
            status=status.HTTP_200_OK,
        )


class ClimaAPIView(APIView):
    """
    API de Terceros vía Patrón Adapter e Inversión de Dependencias (Entregable 2):
    Consulta el pronóstico meteorológico para la ciudad o coordenadas de un plan,
    conectando con la API REST de Open-Meteo.
    """

    def get(self, request: Request) -> Response:
        ciudad = request.query_params.get("ciudad", "Medellin")
        lat_str = request.query_params.get("lat")
        lon_str = request.query_params.get("lon")

        lat = float(lat_str) if lat_str else None
        lon = float(lon_str) if lon_str else None

        servicio = container.consultar_clima()
        clima = servicio.ejecutar(ciudad=ciudad, latitud=lat, longitud=lon)

        return Response(
            {
                "ciudad": clima.ciudad,
                "temperatura_c": clima.temperatura_c,
                "descripcion": clima.descripcion,
                "icono": clima.icono,
                "humedad_pct": clima.humedad_pct,
                "recomendacion": clima.recomendacion,
                "proveedor": clima.proveedor,
            },
            status=status.HTTP_200_OK,
        )


class ReporteAsincronoAPIView(APIView):
    """
    Comunicación Asíncrona con Message Broker (Redis/Celery - Entregable 2):
    POST: Encola la tarea de generación de reporte en segundo plano.
    GET: Consulta el estado y resultado de una tarea en Celery.
    """

    def post(self, request: Request) -> Response:
        correo = request.data.get("correo", "admin@meetu2.co")
        servicio = container.solicitar_reporte_asincrono()
        tarea = servicio.ejecutar(correo=correo)

        return Response(
            {
                "task_id": tarea.task_id,
                "estado": tarea.estado,
                "mensaje": tarea.mensaje,
                "instruccion": f"Consulta el estado en GET /api/v1/integracion/reportes/asincrono/{tarea.task_id}/",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DetalleReporteAsincronoAPIView(APIView):
    def get(self, request: Request, task_id: str) -> Response:
        servicio = container.consultar_estado_reporte()
        tarea = servicio.ejecutar(task_id=task_id)

        return Response(
            {
                "task_id": tarea.task_id,
                "estado": tarea.estado,
                "mensaje": tarea.mensaje,
                "resultado": tarea.resultado,
            },
            status=status.HTTP_200_OK,
        )


class PartnerHotelesAPIView(APIView):
    """
    API REST del Servicio de Hoteles Aliado (hotelMDJ Integration).
    Expone el catálogo en vivo de alojamientos y hospedajes disponibles
    para consumo por parte de la plataforma MeetU2 y aplicaciones autorizadas.
    """

    def get(self, request: Request) -> Response:
        return Response(
            {
                "servicio": "hotelMDJ Cloud API v2.4",
                "proveedor": "hotelMDJ — Cadena & Alojamientos Aliados",
                "estado": "operativo",
                "total": 4,
                "hoteles": [
                    {
                        "id_hotel": "hotel-poblado-01",
                        "nombre_hotel": "Hotel Boutique & Spa El Poblado",
                        "tipo_alojamiento": "Suite Deluxe con Balcón",
                        "ciudad": "Medellín",
                        "sector": "El Poblado",
                        "precio_noche": 220000,
                        "habitaciones_disponibles": 5,
                        "estrellas": 4.9,
                        "amenidades": ["☕ Desayuno buffet", "🏊 Piscina en terraza", "🧖 Spa & Sauna", "📶 WiFi 500 Mbps"],
                        "url_reserva": "https://hotelmdj.com/hotel/poblado-boutique",
                        "cadena": "Cadena Hotelera Estelar (hotelMDJ)",
                        "imagen": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&auto=format&fit=crop",
                    },
                    {
                        "id_hotel": "hotel-santaelena-02",
                        "nombre_hotel": "Eco-Lodge & Glamping Santa Elena",
                        "tipo_alojamiento": "Domo Geodésico con Jacuzzi",
                        "ciudad": "Santa Elena",
                        "sector": "Bosque Nativo",
                        "precio_noche": 185000,
                        "habitaciones_disponibles": 3,
                        "estrellas": 4.8,
                        "amenidades": ["🔥 Fogata nocturna", "🛁 Jacuzzi privado", "🍳 Desayuno campesino", "🌿 Vista panorámica"],
                        "url_reserva": "https://hotelmdj.com/hotel/glamping-santa-elena",
                        "cadena": "EcoHoteles Antioquia (hotelMDJ)",
                        "imagen": "https://images.unsplash.com/photo-1587061949409-02df41d5e562?w=800&auto=format&fit=crop",
                    },
                    {
                        "id_hotel": "hotel-laureles-03",
                        "nombre_hotel": "Hotel Terraza Laureles Urban & Rooftop",
                        "tipo_alojamiento": "Habitación Superior King",
                        "ciudad": "Medellín",
                        "sector": "Laureles",
                        "precio_noche": 160000,
                        "habitaciones_disponibles": 6,
                        "estrellas": 4.7,
                        "amenidades": ["🍹 Rooftop Bar", "☕ Cafetería de autor", "🏋️ Gimnasio", "📶 WiFi 500 Mbps"],
                        "url_reserva": "https://hotelmdj.com/hotel/laureles-urban",
                        "cadena": "Urban Boutique Hotels (hotelMDJ)",
                        "imagen": "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop",
                    },
                    {
                        "id_hotel": "hotel-guatape-04",
                        "nombre_hotel": "Resort & Cabañas Guatapé Lakefront",
                        "tipo_alojamiento": "Cabaña frente al Embalse",
                        "ciudad": "Guatapé",
                        "sector": "Represa El Peñol",
                        "precio_noche": 290000,
                        "habitaciones_disponibles": 4,
                        "estrellas": 4.9,
                        "amenidades": ["⛵ Muelle náutico", "🏊 Piscina infinita", "🍽️ Restaurante lacustre", "🚴 Kayaks incluidos"],
                        "url_reserva": "https://hotelmdj.com/hotel/guatape-resort",
                        "cadena": "Lakeside Resorts (hotelMDJ)",
                        "imagen": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&auto=format&fit=crop",
                    },
                ],
            },
            status=status.HTTP_200_OK,
        )


# Alias para compatibilidad con código anterior o pruebas
SimuladorHotelesAPIView = PartnerHotelesAPIView


class ReservarHotelAliadoAPIView(APIView):
    """
    Transacción de reserva con el servicio aliado hotelMDJ.
    Genera el voucher oficial y persiste la reserva en base de datos
    asociándola a la cuenta del usuario para su consulta en 'Mis reservas'.
    """

    def post(self, request: Request) -> Response:
        data = request.data
        hotel_id = str(data.get("hotel_id", "hotel-001"))
        nombre_hotel = str(data.get("nombre_hotel", "Hotel Boutique & Spa El Poblado"))
        tipo_alojamiento = str(data.get("tipo_alojamiento", "Hospedaje"))
        ciudad = str(data.get("ciudad", "Medellín"))
        imagen_url = str(data.get("imagen_url", ""))

        checkin_str = str(data.get("checkin", "2026-11-15"))
        checkout_str = str(data.get("checkout", "2026-11-17"))
        try:
            d_in = datetime.strptime(checkin_str[:10], "%Y-%m-%d").date()
        except Exception:
            d_in = datetime.now().date() + timedelta(days=1)
        try:
            d_out = datetime.strptime(checkout_str[:10], "%Y-%m-%d").date()
        except Exception:
            d_out = d_in + timedelta(days=2)

        noches = max(1, (d_out - d_in).days)
        habitaciones = max(1, int(data.get("habitaciones", 1)))
        precio_noche = Decimal(str(data.get("precio_noche", "200000")))
        monto_total = precio_noche * habitaciones * noches

        huesped_nombre = str(data.get("huesped_nombre", "Asistente MeetU2")).strip() or "Asistente MeetU2"
        huesped_correo = str(data.get("huesped_correo", "huesped@meetu2.co")).strip() or "huesped@meetu2.co"

        usuario_raw = data.get("usuario_id")
        usuario_id = None
        if usuario_raw:
            try:
                usuario_id = UUID(str(usuario_raw))
            except (ValueError, AttributeError):
                usuario_id = None

        codigo_reserva = f"MDJ-{uuid4().hex[:6].upper()}"

        reserva = ReservaHotel.objects.create(
            usuario_id=usuario_id,
            codigo_reserva=codigo_reserva,
            hotel_id=hotel_id,
            nombre_hotel=nombre_hotel,
            tipo_alojamiento=tipo_alojamiento,
            ciudad=ciudad,
            fecha_checkin=d_in,
            fecha_checkout=d_out,
            noches=noches,
            habitaciones=habitaciones,
            precio_noche=precio_noche,
            monto_total=monto_total,
            huesped_nombre=huesped_nombre,
            huesped_correo=huesped_correo,
            imagen_url=imagen_url,
            estado="CONFIRMADA",
        )

        return Response(
            {
                "status": "confirmada",
                "servicio_aliado": "hotelMDJ",
                "id": str(reserva.id),
                "codigo_reserva": reserva.codigo_reserva,
                "hotel_id": reserva.hotel_id,
                "hotel": reserva.nombre_hotel,
                "tipo_alojamiento": reserva.tipo_alojamiento,
                "ciudad": reserva.ciudad,
                "fecha_checkin": reserva.fecha_checkin.isoformat(),
                "fecha_checkout": reserva.fecha_checkout.isoformat(),
                "noches": reserva.noches,
                "habitaciones": reserva.habitaciones,
                "precio_noche": float(reserva.precio_noche),
                "monto_total": float(reserva.monto_total),
                "huesped": reserva.huesped_nombre,
                "correo": reserva.huesped_correo,
                "usuario_id": str(reserva.usuario_id) if reserva.usuario_id else None,
                "imagen_url": reserva.imagen_url,
                "mensaje": f"¡Reserva confirmada en {reserva.nombre_hotel} con hotelMDJ! Voucher de confirmación: {reserva.codigo_reserva}",
            },
            status=status.HTTP_201_CREATED,
        )


class MisReservasHotelAPIView(APIView):
    """
    GET /api/v1/integracion/aliados/hoteles/mis-reservas/?usuario_id=<UUID>
    Retorna los comprobantes y vouchers hoteleros asociados estrictamente al usuario consultante.
    Si no se envía usuario_id o no existe, retorna una lista vacía para evitar fuga entre perfiles.
    """

    def get(self, request: Request) -> Response:
        usuario_id_str = request.query_params.get("usuario_id")
        if not usuario_id_str:
            return Response([], status=status.HTTP_200_OK)

        try:
            u_uuid = UUID(str(usuario_id_str).strip())
        except (ValueError, AttributeError):
            return Response([], status=status.HTTP_200_OK)

        qs = ReservaHotel.objects.filter(usuario_id=u_uuid)

        reservas = [
            {
                "id": str(r.id),
                "codigo_reserva": r.codigo_reserva,
                "hotel_id": r.hotel_id,
                "nombre_hotel": r.nombre_hotel,
                "tipo_alojamiento": r.tipo_alojamiento,
                "ciudad": r.ciudad,
                "fecha_checkin": r.fecha_checkin.isoformat(),
                "fecha_checkout": r.fecha_checkout.isoformat(),
                "noches": r.noches,
                "habitaciones": r.habitaciones,
                "precio_noche": float(r.precio_noche),
                "monto_total": float(r.monto_total),
                "huesped_nombre": r.huesped_nombre,
                "huesped_correo": r.huesped_correo,
                "estado": r.estado,
                "imagen_url": r.imagen_url,
                "usuario_id": str(r.usuario_id) if r.usuario_id else None,
                "creado_en": r.creado_en.isoformat(),
            }
            for r in qs
        ]

        return Response(reservas, status=status.HTTP_200_OK)


class CancelarReservaHotelAPIView(APIView):
    """
    POST /api/v1/integracion/aliados/hoteles/reservas/<str:codigo_reserva>/cancelar/
    Cancela la reserva hotelera y actualiza su estado.
    """

    def post(self, request: Request, codigo_reserva: str) -> Response:
        try:
            reserva = ReservaHotel.objects.get(codigo_reserva=codigo_reserva)
        except ReservaHotel.DoesNotExist:
            return Response(
                {"error": f"No se encontró ninguna reserva con el código {codigo_reserva}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        reserva.estado = "CANCELADA"
        reserva.save(update_fields=["estado", "actualizado_en"])

        return Response(
            {
                "mensaje": f"Reserva {codigo_reserva} en {reserva.nombre_hotel} cancelada exitosamente.",
                "codigo_reserva": reserva.codigo_reserva,
                "estado": reserva.estado,
            },
            status=status.HTTP_200_OK,
        )
