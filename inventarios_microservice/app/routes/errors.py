from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.utils.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    HTTP_STATUS_MAP
)


def register_error_handlers(app):
    """Registra manejadores de errores globales para la aplicación."""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Maneja errores de validación (400)."""
        return jsonify({
            "error": "Error de validación",
            "mensaje": str(error)
        }), 400
    
    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(error):
        """Maneja errores de autenticación (401)."""
        return jsonify({
            "error": "No autenticado",
            "mensaje": str(error)
        }), 401
    
    @app.errorhandler(ForbiddenError)
    def handle_forbidden_error(error):
        """Maneja errores de autorización (403)."""
        return jsonify({
            "error": "Acceso denegado",
            "mensaje": str(error)
        }), 403
    
    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        """Maneja errores de recurso no encontrado (404)."""
        return jsonify({
            "error": "Recurso no encontrado",
            "mensaje": str(error)
        }), 404
    
    @app.errorhandler(ConflictError)
    def handle_conflict_error(error):
        """Maneja errores de conflicto (409)."""
        return jsonify({
            "error": "Conflicto",
            "mensaje": str(error)
        }), 409
    
    @app.errorhandler(404)
    def handle_404(error):
        """Maneja errores 404 de rutas no encontradas."""
        return jsonify({
            "error": "Ruta no encontrada",
            "mensaje": "El endpoint solicitado no existe"
        }), 404
    
    @app.errorhandler(405)
    def handle_405(error):
        """Maneja errores de método no permitido."""
        return jsonify({
            "error": "Método no permitido",
            "mensaje": "El método HTTP utilizado no está permitido para esta ruta"
        }), 405
    
    @app.errorhandler(500)
    def handle_500(error):
        """Maneja errores internos del servidor."""
        return jsonify({
            "error": "Error interno del servidor",
            "mensaje": "Ocurrió un error inesperado"
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Maneja excepciones HTTP genéricas de Werkzeug."""
        return jsonify({
            "error": error.name,
            "mensaje": error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Maneja cualquier excepción no capturada."""
        # En producción, no exponer detalles del error
        return jsonify({
            "error": "Error inesperado",
            "mensaje": "Ocurrió un error inesperado en el servidor"
        }), 500
