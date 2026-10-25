# MeetU2

**Marketplace de experiencias sociales.** Conecta personas a través de
actividades presenciales reservables: un organizador publica experiencias con
cupo limitado, un asistente las descubre según sus intereses, reserva, paga y
hace check-in el día del evento. La plataforma cobra una comisión por reserva.

> Proyecto de curso — Arquitectura de Software 2026 · Grupo 4 · **Entrega 2:
> Migración a Microservicios, Integración y Resiliencia** (Strangler Pattern, Celery + Redis,
> adaptadores de integración externa, API provista/consumida, i18n y despliegue en AWS).

## Puesta en marcha con Docker (monolito + microservicio + Celery + Redis)

```bash
docker compose up --build
```

| Componente | URL / Puerto |
|---|---|
| Front (vía Nginx) | <http://localhost:8080/> |
| API Monolito → Django | <http://localhost:8080/api/v1/catalogo/experiencias> |
| Servicio Provisto (Integración) | <http://localhost:8080/api/v1/integracion/experiencias-publicas/> |
| Servicio Consumido (Equipo Aliado) | <http://localhost:8080/api/v1/integracion/aliados/planes/> |
| API Terceros (Clima Adapter) | <http://localhost:8080/api/v1/integracion/clima/?ciudad=Bogota> |
| API Estrangulada → Flask Pagos | <http://localhost:8080/api/v2/pagos/salud> |
| Message Broker | Redis en puerto `6379` |
| Tareas en segundo plano | Worker Celery (`celery`) |

Nginx (`nginx/nginx.conf`) actúa como API Gateway, enviando `/api/v2/pagos` al
microservicio Flask (`services/pagos/`) y el resto al monolito. La documentación
completa de arquitectura y la guía de despliegue en AWS EC2 se encuentran en
[`docs/arquitectura_entrega_2.md`](docs/arquitectura_entrega_2.md).

## Puesta en marcha local (solo el monolito)

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # Linux / macOS
pip install -r requirements.txt

cp .env.example .env                # opcional: valores por defecto ya funcionan
python manage.py migrate
python manage.py seed_demo          # escenario de demostración
python manage.py runserver
```

| | |
|---|---|
| Front | <http://127.0.0.1:8000/> |
| API navegable (DRF) | <http://127.0.0.1:8000/api/v1/catalogo/experiencias> |
| Salud | <http://127.0.0.1:8000/healthz> |

```bash
pytest                          # monolito: 167 pruebas
cd services/pagos && pytest     # microservicio de pagos: 37 pruebas
# Total: 204 pruebas unitarias y de integración pasando al 100%
```

Sin Docker el monolito funciona en **modo legado**: `PAGOS_SERVICE_URL` vacío,
la confirmación de reservas acepta una referencia opaca y el front no usa
`/api/v2`. Para probar el microservicio localmente:

```bash
cd services/pagos
pip install -r requirements.txt
MONOLITO_URL=http://127.0.0.1:8000 flask --app wsgi run --port 5000
# y arrancar Django con PAGOS_SERVICE_URL=http://127.0.0.1:5000
```

## Recorrido de demostración

1. **Descubrir** (`/`) → registrarse con nombre y correo (repetir el correo
   devuelve `409`), vincular intereses y buscar experiencias.
2. **Clima y Aliados** (`/`) → consultar pronóstico del clima en tiempo real
   (Open-Meteo vía Adapter) y explorar planes de la red de aliados.
3. **Internacionalización** (`/`) → alternar entre Español e Inglés con el selector
   `ES | EN` en el encabezado.
4. **Soy organizador** (`/organizador/`) → crear el perfil (nace `PENDIENTE`),
   verificar, crear ubicación y publicar experiencias. Disparar generación asíncrona
   de reportes con Celery y consultar su estado en tiempo real.
5. **Descubrir** → reservar un cupo (se descuenta del catálogo al instante;
   reservar dos veces devuelve `409 reserva_duplicada`).
6. **Mis reservas** (`/mis-reservas/`) → pagar y confirmar (procesado por el
   microservicio Flask estrangulado vía API Gateway), o cancelar y ver el reembolso.
7. **Soy organizador** → validar el ticket con el check-in.
8. **Social** → tras el check-in, calificar la experiencia (1 a 5★) con comentario,
   lo cual recalcula la calificación promedio del organizador.

## Arquitectura

Monolito **modular** organizado por contexto acotado, con arquitectura
**hexagonal** dentro de cada módulo:

```
apps/
├── shared/          entidades base · errores → HTTP · Unit of Work · paginación · compile_translations
├── identidad/       Usuario · Organizador · InteresUsuario
├── catalogo/        Experiencia · Ubicacion · CategoriaInteres   ← Builder
├── reservas/        Reserva · políticas de cupo, reembolso y check-in
├── notificaciones/  canales intercambiables (asíncrono con Celery)  ← Factory
├── social/          Reseña · calificaciones post check-in y reputación host
├── integraciones/   API provista · API aliado · Open-Meteo adapter · reportes Celery
├── pagos/           estrangulado → services/pagos (ya no se instala)
└── frontend/        páginas que consumen la API

services/
└── pagos/           microservicio Flask /api/v2/pagos              ← Strangler
nginx/nginx.conf     fachada API Gateway: bifurca /api/v1 y /api/v2/pagos
docker-compose.yml   db · django · pagos · redis · celery · nginx
```

Cada contexto se divide en `domain/` (entidades y reglas puras),
`application/` (casos de uso y puertos), `infrastructure/` (ORM y adaptadores) y
`api/` (serializers y APIViews). **Las dependencias apuntan siempre hacia el
dominio.**

| Requisito de la entrega | Dónde |
|---|---|
| Service Layer, sin lógica en vistas ni modelos | `*/application/services.py` y `*/domain/policies.py` |
| DRF con Serializers, APIView y 201/400/404/409 | `*/api/` y `shared/api/exception_handler.py` |
| **Builder** (entidad más compleja) | `catalogo/application/builders.py` |
| **Factory** (dependencia externa) | `notificaciones/infrastructure/factories.py` · `services/pagos/pagos_service/gateways.py` |
| **Strangler Pattern** | `services/pagos/` · `nginx/nginx.conf` · `docker-compose.yml` |
| **Message Broker (Celery + Redis)** | `config/celery.py` · `apps/notificaciones/tasks.py` · `apps/integraciones/tasks.py` |
| **Servicio a Proveer** | `apps/integraciones/application/use_cases.py::ExponerExperienciasPublicasUseCase` (`/api/v1/integracion/experiencias-publicas/`) |
| **Servicio a Consumir (Aliado)** | `apps/integraciones/domain/ports.py::ServicioAliadoPort` · `HttpServicioAliadoAdapter` |
| **API Terceros (Adapter Pattern)** | `apps/integraciones/domain/ports.py::ClimaPort` · `OpenMeteoClimaAdapter` |
| **Internacionalización (i18n)** | `locale/es/` · `locale/en/` · `apps/shared/management/commands/compile_translations.py` |
| **Despliegue AWS EC2** | Guía paso a paso en `docs/arquitectura_entrega_2.md` |

## Comandos útiles

```bash
python manage.py seed_demo            # datos de demostración
python manage.py compile_translations # compila catálogos .po a binarios .mo
python manage.py expirar_reservas     # libera cupos de reservas vencidas
pytest                                # 167 pruebas del monolito
cd services/pagos && pytest           # 37 pruebas del microservicio
```

## Herramientas usadas

Python 3.14 · Django 6.1 · Django REST Framework 3.18 · Flask 3.1 ·
SQLAlchemy 2.1 · PostgreSQL 17 (Docker) / SQLite (desarrollo) · Nginx 1.27 ·
Docker Compose · gunicorn · pytest.
