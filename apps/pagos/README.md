# Contexto Pagos — estrangulado hacia un microservicio (Taller 02)

Este esqueleto **ya no forma parte del monolito** (se retiró de
`LOCAL_APPS` en `config/settings.py`). La lógica de pagos se implementó
directamente como microservicio Flask independiente siguiendo el
**Strangler Pattern**:

| | |
|---|---|
| Código | [`services/pagos/`](../../services/pagos) |
| Ruta pública | `/api/v2/pagos` (Nginx → Flask) |
| Documentación | [`docs/wiki/Migración-a-Microservicios-(Strangler-Pattern).md`](<../../docs/wiki/Migración-a-Microservicios-(Strangler-Pattern).md>) |

Lo único que queda en Django es la costura de integración:
`apps/reservas/application/ports.py::VerificadorPagoPort` y su adaptador HTTP
`apps/reservas/infrastructure/adapters.py::HttpVerificadorPago`.

Los archivos vacíos de esta carpeta pueden eliminarse cuando el equipo lo
decida; se conservan solo como rastro histórico de la migración.
