import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


@pytest.fixture(scope='session')
def app():
    """Crea una instancia de la aplicación para testing con mocks."""
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['REDIS_SERVICE_URL'] = 'http://localhost:5011'
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'REDIS_SERVICE_URL': 'http://localhost:5011',
    })
    
    yield app


@pytest.fixture(scope='function')
def client(app):
    """Crea un cliente de prueba para hacer requests HTTP."""
    return app.test_client()


@pytest.fixture
def mock_db_session():
    """Mock de la sesión de base de datos."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.delete = MagicMock()
    session.rollback = MagicMock()
    return session


@pytest.fixture
def mock_redis_service():
    """Mock del servicio Redis."""
    with patch('app.services.redis_queue_service.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'message': 'Published'}
        yield mock_post


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
def sample_inventario_dict():
    """Inventario de muestra como diccionario."""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'productoId': 1,
        'cantidad': 100,
        'ubicacion': 'Bodega A - Estante 1',
        'usuarioCreacion': 'admin',
        'fechaCreacion': '2025-10-27T12:00:00',
        'usuarioActualizacion': 'admin',
        'fechaActualizacion': '2025-10-27T12:00:00'
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
