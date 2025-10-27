import pytest
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app as flask_app


@pytest.fixture
def app():
    """Crea la aplicación Flask para testing."""
    flask_app.config.update({
        "TESTING": True,
        "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
        "REDIS_PORT": int(os.getenv("REDIS_PORT", 6379)),
        "REDIS_DB": int(os.getenv("REDIS_DB", 0)),
    })
    
    yield flask_app


@pytest.fixture
def client(app):
    """Cliente de prueba para la aplicación."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner para la aplicación."""
    return app.test_cli_runner()
