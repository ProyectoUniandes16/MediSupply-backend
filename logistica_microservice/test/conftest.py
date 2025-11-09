import pytest
from src import create_app
from src.config.config import Config
from src.models.zona import db


class TestConfig(Config):
    """Configuración para tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-secret-key'


@pytest.fixture
def app():
    """Fixture para crear la aplicación de test"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture para el cliente de test"""
    return app.test_client()


@pytest.fixture
def access_token(app):
    """Fixture para generar un token JWT de prueba"""
    from flask_jwt_extended import create_access_token
    
    with app.app_context():
        token = create_access_token(identity='test-user-id')
        return token
