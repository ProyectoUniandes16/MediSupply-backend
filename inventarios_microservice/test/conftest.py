import pytest
import os
import sys
from flask import Flask

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db


@pytest.fixture(scope='session')
def app():
    """Crea una instancia de la aplicación para testing."""
    # Configurar variables de entorno para testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'  # Base de datos en memoria
    os.environ['REDIS_SERVICE_URL'] = 'http://localhost:5011'
    os.environ['TESTING'] = 'True'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Crea un cliente de prueba para hacer requests HTTP."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Crea una sesión de base de datos para testing."""
    with app.app_context():
        # Limpiar la BD antes de cada test
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield db.session
        db.session.remove()


@pytest.fixture
def sample_inventario_data():
    """Datos de muestra para crear un inventario."""
    return {
        'productoId': 1,
        'cantidad': 100,
        'ubicacion': 'Bodega A - Estante 1',
        'usuario': 'admin'
    }


@pytest.fixture
def sample_producto_data():
    """Datos de muestra para un producto."""
    return {
        'id': 1,
        'nombre': 'Paracetamol 500mg',
        'codigo_sku': 'MED-001',
        'precio_unitario': 1500.00
    }
