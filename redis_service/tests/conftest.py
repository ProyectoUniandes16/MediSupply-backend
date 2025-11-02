import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Asegurar que el paquete principal esté disponible
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app  # noqa: E402  (import after path setup)
from app.services.redis_service import redis_client  # noqa: E402


@pytest.fixture
def redis_connection_mock():
    """Mock básico de conexión Redis usado durante la inicialización."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.keys.return_value = []
    mock.exists.return_value = False
    mock.ttl.return_value = 120
    mock.flushdb.return_value = True
    mock.publish.return_value = 1
    mock.pubsub_channels.return_value = []
    mock.pubsub_numsub.return_value = [("test", 0)]
    mock.info.return_value = {
        'redis_version': '6.2.0',
        'uptime_in_seconds': 100,
        'connected_clients': 5,
        'used_memory_human': '1M',
        'total_commands_processed': 10,
    }
    return mock


@pytest.fixture
def app(redis_connection_mock):
    """Crea la aplicación Flask con Redis mockeado."""
    with patch('app.services.redis_service.redis.Redis', return_value=redis_connection_mock):
        flask_app = create_app()
        flask_app.config.update(TESTING=True)
        try:
            yield flask_app
        finally:
            # Restablecer estado global para evitar fugas entre pruebas
            redis_client.client = None
            redis_client.config = None


@pytest.fixture
def client(app):
    """Cliente HTTP de prueba."""
    return app.test_client()
