import pytest
from flask import Blueprint
from werkzeug.exceptions import BadRequest, InternalServerError
from app.utils.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError
)
from app import create_app
from unittest.mock import patch

class TestErrors:

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test to allow route registration."""
        with patch('app.__init__.db.Model.metadata.reflect', return_value=None), \
             patch('app.__init__.db.create_all', return_value=None):
            app = create_app()
            app.config['TESTING'] = True
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            yield app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_validation_error(self, app, client):
        @app.route('/test-validation')
        def raise_validation():
            raise ValidationError("Invalid input")
        
        response = client.get('/test-validation')
        assert response.status_code == 400
        assert response.json['error'] == "Error de validación"

    def test_unauthorized_error(self, app, client):
        @app.route('/test-unauthorized')
        def raise_unauthorized():
            raise UnauthorizedError("Login required")
        
        response = client.get('/test-unauthorized')
        assert response.status_code == 401
        assert response.json['error'] == "No autenticado"

    def test_forbidden_error(self, app, client):
        @app.route('/test-forbidden')
        def raise_forbidden():
            raise ForbiddenError("Access denied")
        
        response = client.get('/test-forbidden')
        assert response.status_code == 403
        assert response.json['error'] == "Acceso denegado"

    def test_not_found_error(self, app, client):
        @app.route('/test-not-found-exc')
        def raise_not_found():
            raise NotFoundError("Item not found")
        
        response = client.get('/test-not-found-exc')
        assert response.status_code == 404
        assert response.json['error'] == "Recurso no encontrado"

    def test_conflict_error(self, app, client):
        @app.route('/test-conflict')
        def raise_conflict():
            raise ConflictError("Item exists")
        
        response = client.get('/test-conflict')
        assert response.status_code == 409
        assert response.json['error'] == "Conflicto"

    def test_404_route(self, client):
        response = client.get('/non-existent-route')
        assert response.status_code == 404
        assert response.json['error'] == "Ruta no encontrada"

    def test_405_method(self, app, client):
        @app.route('/test-method', methods=['GET'])
        def test_method():
            return "ok"
        
        response = client.post('/test-method')
        assert response.status_code == 405
        assert response.json['error'] == "Método no permitido"

    def test_500_error(self, app, client):
        @app.route('/test-500')
        def raise_500():
            raise InternalServerError("Server boom")
        
        response = client.get('/test-500')
        assert response.status_code == 500
        assert response.json['error'] == "Error interno del servidor"

    def test_http_exception(self, app, client):
        @app.route('/test-http')
        def raise_http():
            raise BadRequest("Bad request")
        
        response = client.get('/test-http')
        assert response.status_code == 400
        assert response.json['error'] == "Bad Request"

    def test_generic_exception(self, app, client):
        @app.route('/test-generic')
        def raise_generic():
            raise Exception("Whoops")
        
        # Flask propagates exceptions in testing mode unless PRESERVE_CONTEXT_ON_EXCEPTION is False
        # or we catch it. But the error handler should catch it if configured.
        # However, in debug/testing mode, Flask might re-raise.
        # We need to ensure the error handler is called.
        app.config['PROPAGATE_EXCEPTIONS'] = False
        app.config['TESTING'] = False # Disable testing mode to trigger error handler for generic exception
        
        response = client.get('/test-generic')
        assert response.status_code == 500
        assert response.json['error'] == "Error inesperado"
