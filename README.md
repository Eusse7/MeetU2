# MeetU2

**Marketplace de experiencias sociales.** Conecta personas a través de
actividades presenciales reservables: un organizador publica experiencias con
cupo limitado, un asistente las descubre según sus intereses, reserva, paga y
hace check-in el día del evento. La plataforma cobra una comisión por reserva.

> Proyecto de curso — Arquitectura de Software 2026 · Grupo 4 · **Entrega 1:
> núcleo de negocio y exposición de API** · **Taller 02: Strangler Pattern**
> (Pagos extraído a un microservicio Flask).

## Puesta en marcha con Docker (monolito + microservicio)

```bash
docker compose up --build
```

| | |
|---|---|
| Front (vía Nginx) | <http://localhost:8080/> |
| API legada → Django | <http://localhost:8080/api/v1/catalogo/experiencias> |
| API estrangulada → Flask | <http://localhost:8080/api/v2/pagos/salud> |

Nginx (`nginx/nginx.conf`) envía `/api/v2/pagos` al microservicio Flask
(`services/pagos/`) y todo lo demás al monolito. La justificación, la matriz de
decisión y los diagramas están en
[`docs/wiki/Migración a Microservicios (Strangler Pattern)`](<docs/wiki/Migración-a-Microservicios-(Strangler-Pattern).md>).

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
pytest                          # monolito: 117 pruebas
cd services/pagos && pytest     # microservicio de pagos: 37 pruebas
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
2. **Soy organizador** (`/organizador/`) → crear el perfil (nace `PENDIENTE`),
   intentar publicar sin verificar (`409`), verificar, crear ubicación y
   publicar. Un cupo mayor al aforo devuelve `400 aforo_excedido`.
3. **Descubrir** → reservar un cupo (se descuenta del catálogo al instante;
   reservar dos veces devuelve `409 reserva_duplicada`).
4. **Mis reservas** (`/mis-reservas/`) → pagar y confirmar, o cancelar y ver el
   reembolso calculado según la antelación.
5. **Soy organizador** → validar el ticket con el check-in.

## Arquitectura

Monolito **modular** organizado por contexto acotado, con arquitectura
**hexagonal** dentro de cada módulo:

```
apps/
├── shared/          entidades base · errores → HTTP · Unit of Work · paginación
├── identidad/       Usuario · Organizador · InteresUsuario
├── catalogo/        Experiencia · Ubicacion · CategoriaInteres   ← Builder
├── reservas/        Reserva · políticas de cupo, reembolso y check-in
├── notificaciones/  canales intercambiables                       ← Factory
├── social/          previsto para la Entrega 2
├── pagos/           estrangulado → services/pagos (ya no se instala)
└── frontend/        páginas que consumen la API

services/
└── pagos/           microservicio Flask /api/v2/pagos              ← Strangler
nginx/nginx.conf     fachada: bifurca /api/v1 (Django) y /api/v2/pagos (Flask)
docker-compose.yml   db · django · pagos · nginx
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
| **Strangler Pattern** (Taller 02) | `services/pagos/` · `nginx/nginx.conf` · `docker-compose.yml` · `reservas/infrastructure/adapters.py::HttpVerificadorPago` |




## Comandos útiles

```bash
python manage.py seed_demo          # datos de demostración
python manage.py expirar_reservas   # libera cupos de reservas vencidas
pytest apps/reservas                # pruebas de un contexto
pytest -m django_db                 # solo pruebas de integración HTTP
```

## Herramientas usadas

Python 3.14 · Django 6.1 · Django REST Framework 3.18 · Flask 3.1 ·
SQLAlchemy 2.1 · PostgreSQL 17 (Docker) / SQLite (desarrollo) · Nginx 1.27 ·
Docker Compose · gunicorn · pytest.
