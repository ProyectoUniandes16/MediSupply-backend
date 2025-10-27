import pytest
from flask import Flask
from src.blueprints.health import health_bp

@pytest.fixture
def client():
    """Fixture que crea un cliente de prueba."""
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.config['TESTING'] = True
    return app.test_client()


def test_health_check_status_code(client):
    """Verifica que el endpoint /health retorne 200 OK."""
    response = client.get('/health')
    assert response.status_code == 200


def test_health_check_json_response(client):
    """Verifica que el endpoint /health retorne JSON válido."""
    response = client.get('/health')
    assert response.content_type == 'application/json'
    
    data = response.get_json()
    assert data is not None


def test_health_check_response_structure(client):
    """Verifica la estructura de la respuesta del health check."""
    response = client.get('/health')
    data = response.get_json()
    
    # Verificar campos esperados
    assert 'status' in data
    assert 'service' in data
    
    # Verificar valores
    assert data['status'] == 'healthy'
    assert data['service'] == 'auth-usuario'


def test_health_check_method_not_allowed(client):
    """Verifica que otros métodos HTTP no estén permitidos."""
    response = client.post('/health')
    assert response.status_code == 405  # Method Not Allowed
    
    response = client.put('/health')
    assert response.status_code == 405
    
    response = client.delete('/health')
    assert response.status_code == 405
