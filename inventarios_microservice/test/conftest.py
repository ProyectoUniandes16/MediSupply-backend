import os
import sys
import pytest
from unittest.mock import patch

# Asegurar que el paquete principal esté en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


@pytest.fixture(scope='session')
def app():
    """Configura la aplicación Flask para pruebas sin tocar una base real."""
    os.environ.setdefault('TESTING', 'True')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    os.environ.setdefault('REDIS_SERVICE_URL', 'http://redis-service.test')
    with patch('app.__init__.db.Model.metadata.reflect', return_value=None), \
         patch('app.__init__.db.create_all', return_value=None):
        flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        REDIS_SERVICE_URL='http://redis-service.test',
    )
    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Cliente HTTP de prueba."""
    return app.test_client()


@pytest.fixture(autouse=True)
def disable_queue(mocker):
    """Evita llamadas reales al servicio de cola durante las pruebas."""
    return mocker.patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update', return_value=True)


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
