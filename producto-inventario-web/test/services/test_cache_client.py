import pytest
from unittest.mock import Mock, patch
from src.services.cache_client import CacheClient


class TestCacheClient:
    """Tests para el cliente de cache (Redis Service)."""
    
    @pytest.fixture
    def cache_client(self):
        """Fixture que crea una instancia del cliente de cache."""
        return CacheClient('http://redis_service:5011')
    
    # ==================== TESTS DE GET ====================
    
    @patch('src.services.cache_client.requests.get')
    def test_get_cache_hit(self, mock_get, cache_client):
        """Test: Obtener dato del cache (cache hit)."""
        # Arrange
        key = 'inventarios:producto:1'
        cached_value = {
            'inventarios': [
                {'id': '123', 'cantidad': 100}
            ],
            'totalCantidad': 100
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'found': True,
            'value': cached_value
        }
        mock_get.return_value = mock_response
        
        # Act
        result = cache_client.get(key)
        
        # Assert
        assert result == cached_value
        mock_get.assert_called_once()
        assert '/api/cache/' + key in mock_get.call_args[0][0]
    
    @patch('src.services.cache_client.requests.get')
    def test_get_cache_miss(self, mock_get, cache_client):
        """Test: Obtener dato del cache (cache miss)."""
        # Arrange
        key = 'inventarios:producto:999'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'found': False,
            'value': None
        }
        mock_get.return_value = mock_response
        
        # Act
        result = cache_client.get(key)
        
        # Assert
        assert result is None
        mock_get.assert_called_once()
    
    @patch('src.services.cache_client.requests.get')
    def test_get_cache_error(self, mock_get, cache_client):
        """Test: Error al consultar el cache."""
        # Arrange
        key = 'inventarios:producto:1'
        mock_get.side_effect = Exception("Connection error")
        
        # Act
        result = cache_client.get(key)
        
        # Assert
        assert result is None  # Debe retornar None en caso de error
        mock_get.assert_called_once()
    
    @patch('src.services.cache_client.requests.get')
    def test_get_cache_timeout(self, mock_get, cache_client):
        """Test: Timeout al consultar el cache."""
        # Arrange
        key = 'inventarios:producto:1'
        mock_get.side_effect = Exception("Request timeout")
        
        # Act
        result = cache_client.get(key)
        
        # Assert
        assert result is None
    
    # ==================== TESTS DE SET ====================
    
    @patch('src.services.cache_client.requests.post')
    def test_set_cache_success(self, mock_post, cache_client):
        """Test: Establecer valor en cache exitosamente."""
        # Arrange
        key = 'inventarios:producto:1'
        value = {
            'inventarios': [
                {'id': '123', 'cantidad': 100}
            ]
        }
        ttl = 3600
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'mensaje': 'Cache actualizado',
            'key': key
        }
        mock_post.return_value = mock_response
        
        # Act
        result = cache_client.set(key, value, ttl)
        
        # Assert
        assert result is True
        mock_post.assert_called_once()
    
    @patch('src.services.cache_client.requests.post')
    def test_set_cache_error(self, mock_post, cache_client):
        """Test: Error al establecer valor en cache."""
        # Arrange
        key = 'inventarios:producto:1'
        value = {'test': 'data'}
        mock_post.side_effect = Exception("Connection error")
        
        # Act
        result = cache_client.set(key, value)
        
        # Assert
        assert result is False
    
    @patch('src.services.cache_client.requests.post')
    def test_set_cache_with_default_ttl(self, mock_post, cache_client):
        """Test: Establecer cache con TTL por defecto."""
        # Arrange
        key = 'test:key'
        value = {'data': 'test'}
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        # Act
        cache_client.set(key, value)
        
        # Assert
        call_args = mock_post.call_args
        assert 'ttl' in call_args[1]['json']  # Debe incluir TTL
    
    # ==================== TESTS DE DELETE ====================
    
    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_success(self, mock_delete, cache_client):
        """Test: Eliminar clave del cache exitosamente."""
        # Arrange
        key = 'inventarios:producto:1'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'mensaje': 'Cache eliminado',
            'deleted': 1
        }
        mock_delete.return_value = mock_response
        
        # Act
        result = cache_client.delete(key)
        
        # Assert
        assert result is True
        mock_delete.assert_called_once()
    
    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_key_not_found(self, mock_delete, cache_client):
        """Test: Eliminar clave que no existe en cache."""
        # Arrange
        key = 'inventarios:producto:999'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'mensaje': 'Cache eliminado',
            'deleted': 0  # No se eliminó nada
        }
        mock_delete.return_value = mock_response
        
        # Act
        result = cache_client.delete(key)
        
        # Assert
        assert result is True  # Operación exitosa aunque no había nada
    
    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_error(self, mock_delete, cache_client):
        """Test: Error al eliminar del cache."""
        # Arrange
        key = 'test:key'
        mock_delete.side_effect = Exception("Connection error")
        
        # Act
        result = cache_client.delete(key)
        
        # Assert
        assert result is False
    
    # ==================== TESTS DE RESILIENCIA ====================
    
    @patch('src.services.cache_client.requests.get')
    def test_cache_service_unavailable(self, mock_get, cache_client):
        """Test: Cache service no disponible (debe degradar gracefully)."""
        # Arrange
        key = 'test:key'
        mock_get.side_effect = Exception("Service unavailable")
        
        # Act
        result = cache_client.get(key)
        
        # Assert
        assert result is None  # No debe lanzar excepción
    
    @patch('src.services.cache_client.requests.get')
    def test_cache_invalid_json_response(self, mock_get, cache_client):
        """Test: Respuesta inválida del cache service."""
        # Arrange
        key = 'test:key'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        # Act
        result = cache_client.get(key)
        
        # Assert
        assert result is None
    
    @patch('src.services.cache_client.requests.post')
    def test_cache_set_network_timeout(self, mock_post, cache_client):
        """Test: Timeout de red al establecer cache."""
        # Arrange
        key = 'test:key'
        value = {'data': 'test'}
        mock_post.side_effect = Exception("Connection timeout")
        
        # Act
        result = cache_client.set(key, value)
        
        # Assert
        assert result is False
