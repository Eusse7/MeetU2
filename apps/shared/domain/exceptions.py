class DomainError(Exception):
    """Error de negocio. Mapea a 400."""
    codigo = "domain_error"
    status_code = 400

    def __init__(self, mensaje: str, codigo: str | None = None):
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo
        super().__init__(mensaje)


class NotFoundError(DomainError):
    """El recurso no existe. Mapea a 404."""
    codigo = "not_found"
    status_code = 404


class ConflictError(DomainError):
    """El estado actual impide la operación. Mapea a 409."""
    codigo = "conflict"
    status_code = 409


class ValidationError(DomainError):
    codigo = "validation_error"
    status_code = 400