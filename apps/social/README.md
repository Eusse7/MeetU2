# Contexto Social

Módulo implementado con arquitectura hexagonal para gestionar la reputación y las reseñas de experiencias y organizadores en MeetU2.

## Responsabilidad y Reglas de Negocio

1. **Entidad `Resena`**: Vincula una reserva realizada y asistida con una valoración numérica de 1 a 5 estrellas y un comentario opcional.
2. **Evidencia de Asistencia (Regla central)**: Solo puede calificar quien cuenta con una reserva en estado `CHECK_IN` con marca de tiempo `check_in_en` válida y que pertenezca al usuario calificador. Cualquier intento previo arroja `409 reserva_sin_check_in` o `409 reserva_no_pertenece_a_usuario`.
3. **Unicidad de Reseña**: Una reserva solo puede recibir una reseña. Un segundo intento devuelve `409 resena_duplicada`.
4. **Recálculo Reactivo de Reputación**: Cada vez que se crea una reseña, se recalculan las calificaciones del organizador y se actualiza `Organizador.calificacion_promedio` mediante el puerto `OrganizadorCalificacionPort`.

## Estructura Hexagonal

```
apps/social/
├── domain/
│   ├── models.py           # Entidad Resena (UUID, BaseEntity, constraints)
│   ├── enums.py            # EstadoResena (PUBLICADA, OCULTA)
│   ├── exceptions.py       # ResenaNoEncontrada, ReservaSinCheckIn, ResenaDuplicada, etc.
│   └── policies.py         # PoliticaResena (asistencia, rango 1-5), CalculadoraPromedio
├── application/
│   ├── dtos.py             # CrearResenaDTO, MetricasOrganizadorDTO, MetricasExperienciaDTO
│   ├── ports.py            # ReservaAsistenciaPort, OrganizadorCalificacionPort, ResenaRepositoryPort
│   └── services.py         # CrearResenaService, ObtenerResenaService, ListarResenas, Metricas
├── infrastructure/
│   ├── repositories.py     # DjangoResenaRepository (ORM)
│   └── adapters.py         # ReservaAsistenciaAdapter, IdentidadOrganizadorCalificacionAdapter
├── api/
│   ├── serializers.py      # CrearResenaSerializer, ResenaSerializer, MetricasSerializer
│   ├── views.py            # APIViews con respuestas 201/200/400/404/409
│   └── urls.py             # Rutas /api/v1/social/...
├── container.py            # Composition Root del contexto
└── tests/
    ├── test_policies.py    # Pruebas unitarias de políticas puras de dominio
    ├── test_services.py    # Pruebas de casos de uso con dobles en memoria
    └── test_api.py         # Pruebas de integración HTTP sobre DRF
```

## Endpoints de la API

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| `POST` | `/api/v1/social/resenas` | Publicar una nueva reseña tras check-in | `201`, `400`, `404`, `409` |
| `GET` | `/api/v1/social/resenas?usuario_id={id}` | Listar reseñas dejadas por un usuario | `200`, `400` |
| `GET` | `/api/v1/social/resenas/{id}` | Detalle de una reseña | `200`, `404` |
| `GET` | `/api/v1/social/reservas/{id}/resena` | Reseña asociada a una reserva | `200`, `404` |
| `GET` | `/api/v1/social/experiencias/{id}/resenas` | Listar reseñas de una experiencia | `200` |
| `GET` | `/api/v1/social/experiencias/{id}/metricas` | Promedio y total de reseñas de experiencia | `200` |
| `GET` | `/api/v1/social/organizadores/{id}/resenas` | Listar reseñas recibidas por un organizador | `200` |
| `GET` | `/api/v1/social/organizadores/{id}/metricas` | Promedio, total y desglose (1 a 5★) del host | `200` |
