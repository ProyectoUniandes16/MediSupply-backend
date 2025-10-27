class ServiceError(Exception):
    """Base para errores de la capa de servicios."""
    def __init__(self, message):
        self.message = message
        super().__init__(str(message))


class ValidationError(ServiceError):
    """Error por datos inválidos (400)."""
    pass


class NotFoundError(ServiceError):
    """Recurso no encontrado (404)."""
    pass


class ConflictError(ServiceError):
    """Conflicto de estado/únicos (409)."""
    pass


class UnauthorizedError(ServiceError):
    """No autenticado (401)."""
    pass


class ForbiddenError(ServiceError):
    """Autenticado pero sin permisos (403)."""
    pass


# Útil si quieres mapear a HTTP en un solo sitio (p. ej., routes/errors.py)
HTTP_STATUS_MAP = {
    ValidationError: 400,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
    ConflictError: 409,
}
