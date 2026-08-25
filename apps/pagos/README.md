# Contexto Pagos — planificado para la Entrega 2

Estructura creada, sin implementar en la Entrega 1.

Alcance previsto: entidad `Pago`, `PasarelaPort` con una **Factory** que
seleccione la implementación (`fake` / `wompi`) según `PASARELA_PAGO`, y
desembolso al organizador descontando la comisión de plataforma.

Punto de integración ya preparado: `ConfirmarReservaService` recibe hoy la
referencia de pago como dato opaco; cuando exista este contexto se le inyectará
un `PagoPort` y el resto del servicio no cambia.
