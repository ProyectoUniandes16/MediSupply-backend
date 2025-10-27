"""
Tests de integración para las rutas de cache del Redis Service
"""
import pytest
import json


@pytest.mark.integration
class TestCacheRoutes:
    """Tests para las rutas de cache."""
    
    def test_cache_set_and_get(self, client):
        """Test: Establecer y obtener un valor del cache."""
        # Arrange
        test_data = {
            'key': 'test_key',
            'value': {'name': 'Test Product', 'quantity': 100},
            'ttl': 3600
        }
        
        # Act - Set
        response = client.post('/api/cache/', 
                             json=test_data,
                             content_type='application/json')
        
        # Assert - Set
        assert response.status_code == 201
    
    def test_cache_get_nonexistent(self, client):
        """Test: Obtener clave que no existe retorna 404."""
        # Act
        response = client.get('/api/cache/nonexistent_key')
        
        # Assert
        assert response.status_code == 404
        result = response.get_json()
        assert 'message' in result
        assert result['key'] == 'nonexistent_key'
    
    def test_cache_delete(self, client):
        """Test de eliminar clave del cache."""
        # Primero guardar
        data = {
            "key": "test_key_delete",
            "value": {"test": "data"}
        }
        client.post(
            '/api/cache/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Eliminar
        response = client.delete('/api/cache/test_key_delete')
        assert response.status_code == 200
        
        result = response.get_json()
        assert 'message' in result
        assert result['key'] == 'test_key_delete'
        
        # Verificar que ya no existe
        response = client.get('/api/cache/test_key_delete')
        assert response.status_code == 404
    
    def test_cache_set_invalid_data(self, client):
        """Test: Intentar establecer cache sin datos requeridos."""
        # Arrange - Sin 'key'
        invalid_data = {
            'value': {'test': 'data'}
        }
        
        # Act
        response = client.post('/api/cache/',
                             json=invalid_data,
                             content_type='application/json')
    
    def test_cache_with_ttl(self, client):
        """Test: Establecer cache con TTL específico."""
        # Arrange
        test_data = {
            'key': 'ttl_test_key',
            'value': {'temp': 'data'},
            'ttl': 60  # 1 minuto
        }
        
        # Act
        response = client.post('/api/cache/',
                             json=test_data,
                             content_type='application/json')
