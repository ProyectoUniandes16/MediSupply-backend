import pytest
import tempfile
import os
from app import create_app
from app.extensions import db

@pytest.fixture
def app(monkeypatch):
    """Crear aplicación de prueba"""
    monkeypatch.setenv('TESTING', 'true')  # Fuerza configuración de pruebas desde create_app
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')

    app = create_app()
    # Usar la configuración específica de testing
    app.config.from_object('app.config.TestingConfig')
    
    # Override del directorio de uploads para tests (usar directorio temporal)
    temp_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = temp_dir
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Limpiar directorio temporal después de tests
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def client(app):
    """Cliente de prueba para hacer requests"""
    return app.test_client()
