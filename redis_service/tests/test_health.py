"""
Tests para el health check del Redis Service
"""
import pytest


@pytest.mark.unit
def test_health_check(client):
    """Test del endpoint de health check."""
    response = client.get('/health')
    
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert 'status' in data
    assert data['status'] == 'healthy'
    assert 'service' in data
    assert data['service'] == 'redis_service'
    assert 'redis' in data


@pytest.mark.unit
def test_health_check_structure(client):
    """Test de la estructura completa del health check."""
    response = client.get('/health')
    data = response.get_json()
    
    # Verificar estructura
    required_fields = ['status', 'service', 'redis', 'port']
    for field in required_fields:
        assert field in data, f"Campo '{field}' faltante en respuesta"
    
    # Verificar tipos y valores
    assert isinstance(data['status'], str)
    assert isinstance(data['service'], str)
    assert isinstance(data['port'], int)
    assert data['redis'] in ['connected', 'disconnected']

