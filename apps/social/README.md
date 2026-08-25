# Contexto Social — planificado para la Entrega 2

Estructura creada, sin implementar en la Entrega 1.

Alcance previsto: entidad `Reseña` con la regla de negocio que la sostiene —
solo puede calificar quien tiene una reserva en estado `CHECK_IN` — y
recálculo de `Organizador.calificacion_promedio`.

Punto de integración ya preparado: `Reserva.estado == CHECK_IN` y
`Reserva.check_in_en` son la evidencia de asistencia que este contexto
consultará mediante un puerto.
