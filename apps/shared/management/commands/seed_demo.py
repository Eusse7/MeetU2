"""
Carga un escenario de demostracion completo para la sustentacion.

Importante: el comando NO escribe en la base de datos por su cuenta. Invoca los
mismos casos de uso que expone la API, asi que todo lo que se cree aqui ha
pasado por las mismas validaciones de negocio que pasaria por HTTP.

    python manage.py seed_demo
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalogo import container as catalogo
from apps.catalogo.application.dtos import (
    CrearCategoriaDTO,
    CrearUbicacionDTO,
    PublicarExperienciaDTO,
)
from apps.identidad import container as identidad
from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
    VincularInteresDTO,
)
from apps.reservas import container as reservas
from apps.reservas.application.dtos import (
    CheckInDTO,
    ConfirmarReservaDTO,
    SolicitarReservaDTO,
)
from apps.social import container as social
from apps.social.application.dtos import CrearResenaDTO

CATEGORIAS = [
    ("Gastronomia", "Catas, cenas y talleres de cocina"),
    ("Aire libre", "Senderismo, ciclismo y actividades al aire libre"),
    ("Musica", "Conciertos intimos y jam sessions"),
    ("Juegos de mesa", "Noches de board games y rol"),
]

UBICACIONES = [
    ("Casa Rosé", "Cra 35 #8A-3", "Medellin", 6.2087, -75.5675, 40),
    ("Parque Arvi", "Vereda Piedras Blancas", "Medellin", 6.2795, -75.5019, 120),
    ("Sala Tropical", "Cl 53 #43-91", "Medellin", 6.2518, -75.5636, 25),
]


class Command(BaseCommand):
    help = "Crea usuarios, categorias, ubicaciones y experiencias de ejemplo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Limpia la base de datos antes de sembrar los datos de demo.",
        )

    def handle(self, *args, **opciones):
        if opciones.get("limpiar"):
            self.stdout.write("Limpiando base de datos...")
            from django.core.management import call_command
            call_command("flush", interactive=False)

        ahora = timezone.now()

        self.stdout.write("Creando categorias de interes...")
        categorias = {}
        for nombre, descripcion in CATEGORIAS:
            categoria = catalogo.crear_categoria().ejecutar(
                CrearCategoriaDTO(nombre=nombre, descripcion=descripcion)
            )
            categorias[nombre] = categoria
            self.stdout.write(f"  - {categoria.nombre} ({categoria.id})")

        self.stdout.write("Creando ubicaciones...")
        ubicaciones = []
        for nombre, direccion, ciudad, lat, lon, aforo in UBICACIONES:
            ubicaciones.append(
                catalogo.crear_ubicacion().ejecutar(
                    CrearUbicacionDTO(
                        nombre=nombre,
                        direccion=direccion,
                        ciudad=ciudad,
                        latitud=lat,
                        longitud=lon,
                        aforo_maximo=aforo,
                    )
                )
            )

        self.stdout.write("Creando organizador verificado...")
        host = identidad.registrar_usuario().ejecutar(
            RegistrarUsuarioDTO(nombre="Laura Host", correo="laura@meetu2.co")
        )
        organizador = identidad.convertir_en_organizador().ejecutar(
            ConvertirEnOrganizadorDTO(
                id_usuario=host.id,
                nombre_comercial="Colectivo Cafe & Ritmo",
                cuenta_bancaria="123456789",
            )
        )
        identidad.verificar_organizador().ejecutar(organizador.id, True)

        self.stdout.write("Creando asistente con intereses...")
        asistente = identidad.registrar_usuario().ejecutar(
            RegistrarUsuarioDTO(nombre="Andres Asistente", correo="andres@meetu2.co")
        )
        for nombre, nivel in (("Gastronomia", 5), ("Musica", 4)):
            identidad.vincular_interes().ejecutar(
                VincularInteresDTO(
                    id_usuario=asistente.id,
                    id_categoria=categorias[nombre].id,
                    nivel_afinidad=nivel,
                )
            )

        self.stdout.write("Publicando experiencias...")
        catalogo_experiencias = [
            ("Cata de cafes de origen", "Gastronomia", 0, Decimal("45000"), 12, 2),
            ("Caminata al amanecer en Arvi", "Aire libre", 1, Decimal("30000"), 20, 4),
            ("Jam session de bolero", "Musica", 2, Decimal("25000"), 15, 6),
            ("Noche de juegos de mesa", "Juegos de mesa", 0, Decimal("18000"), 10, 8),
        ]
        for titulo, categoria, idx_ubicacion, precio, cupo, dias in catalogo_experiencias:
            experiencia = catalogo.publicar_experiencia().ejecutar(
                PublicarExperienciaDTO(
                    id_organizador=organizador.id,
                    id_ubicacion=ubicaciones[idx_ubicacion].id,
                    titulo=titulo,
                    descripcion=f"Experiencia de {categoria.lower()} en Medellin.",
                    fecha_hora=ahora + timedelta(days=dias),
                    precio=precio,
                    cupo_maximo=cupo,
                    categorias=(categorias[categoria].id,),
                )
            )
            self.stdout.write(f"  - {experiencia.titulo} ({experiencia.id})")

        # Experiencia para hoy dentro de la ventana de check-in (2.5 horas adelante)
        exp_hoy = catalogo.publicar_experiencia().ejecutar(
            PublicarExperienciaDTO(
                id_organizador=organizador.id,
                id_ubicacion=ubicaciones[0].id,
                titulo="Taller de Barismo y Espresso",
                descripcion="Taller practico de calibracion de espresso en Casa Rose.",
                fecha_hora=ahora + timedelta(hours=2, minutes=30),
                precio=Decimal("40000"),
                cupo_maximo=8,
                categorias=(categorias["Gastronomia"].id,),
            )
        )
        self.stdout.write(f"  - {exp_hoy.titulo} ({exp_hoy.id}) [evento de hoy]")

        self.stdout.write("Creando reserva con check-in y reseña de demostracion...")
        reserva_demo = reservas.solicitar_reserva().ejecutar(
            SolicitarReservaDTO(
                id_usuario=asistente.id,
                id_experiencia=exp_hoy.id,
                cantidad_cupos=1,
            )
        )
        reservas.confirmar_reserva().ejecutar(
            ConfirmarReservaDTO(
                id_reserva=reserva_demo.id,
                referencia_pago="DEMO-REF-001",
            )
        )
        reservas.registrar_check_in().ejecutar(
            CheckInDTO(
                codigo_ticket=reserva_demo.codigo_ticket,
                id_organizador=organizador.id,
            )
        )
        resena_demo = social.crear_resena().ejecutar(
            CrearResenaDTO(
                id_reserva=reserva_demo.id,
                id_usuario=asistente.id,
                calificacion=5,
                comentario="Increible taller de barismo! El cafe y la explicacion de Laura fueron excepcionales.",
            )
        )
        self.stdout.write(f"  - Resena registrada: {resena_demo.calificacion}* ({resena_demo.id})")

        self.stdout.write(self.style.SUCCESS("\nEscenario de demo listo."))
        self.stdout.write(f"  Asistente   : andres@meetu2.co  ({asistente.id})")
        self.stdout.write(f"  Organizador : laura@meetu2.co   ({organizador.id})")
