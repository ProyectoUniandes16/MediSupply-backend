import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.inventarios_service import InventariosService


class TestInventariosService:
    """Tests para el servicio de inventarios del BFF."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de la configuración de la app."""
        config = {
            'INVENTARIOS_URL': 'http://inventarios:5009',
            'REDIS_SERVICE_URL': 'http://redis_service:5011'
        }
        return config
    
    @pytest.fixture
    def inventarios_service(self, mock_config):
        """Fixture que crea una instancia del servicio."""
        return InventariosService(mock_config)
    
    # ==================== TESTS DE CACHE ====================
    
    @patch('src.services.inventarios_service.CacheClient')
    @patch('src.services.inventarios_service.requests.get')
    def test_get_inventarios_by_producto_cache_hit(self, mock_get, mock_cache_client, inventarios_service):
        """Test: Consultar inventarios desde cache (cache hit)."""
        # Arrange
        producto_id = 1
        cached_data = {
            'inventarios': [
                {'id': '123', 'cantidad': 100, 'ubicacion': 'Bodega A'}
            ],
            'totalCantidad': 100
        }
        
        mock_cache = MagicMock()
        mock_cache.get.return_value = cached_data
        mock_cache_client.return_value = mock_cache
        
        # Act
        result = inventarios_service.get_inventarios_by_producto(producto_id)
        
        # Assert
        assert result['source'] == 'cache'
        assert result['productoId'] == str(producto_id)
        assert result['inventarios'] == cached_data['inventarios']
        assert result['totalCantidad'] == 100
        mock_get.assert_not_called()  # No debe llamar al microservicio
    
    @patch('src.services.inventarios_service.CacheClient')
    @patch('src.services.inventarios_service.requests.get')
    def test_get_inventarios_by_producto_cache_miss(self, mock_get, mock_cache_client, inventarios_service):
        """Test: Consultar inventarios desde microservicio (cache miss)."""
        # Arrange
        producto_id = 1
        microservice_data = [
            {'id': '123', 'productoId': 1, 'cantidad': 100, 'ubicacion': 'Bodega A'}
        ]
        
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # Cache miss
        mock_cache_client.return_value = mock_cache
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = microservice_data
        mock_get.return_value = mock_response
        
        # Act
        result = inventarios_service.get_inventarios_by_producto(producto_id)
        
        # Assert
        assert result['source'] == 'microservice'
        assert result['productoId'] == str(producto_id)
        assert len(result['inventarios']) == 1
        assert result['totalCantidad'] == 100
        mock_get.assert_called_once()
    
    @patch('src.services.inventarios_service.CacheClient')
    @patch('src.services.inventarios_service.requests.get')
    def test_get_inventarios_by_producto_cache_error_fallback(self, mock_get, mock_cache_client, inventarios_service):
        """Test: Si el cache falla, debe hacer fallback al microservicio."""
        # Arrange
        producto_id = 1
        microservice_data = [
            {'id': '123', 'productoId': 1, 'cantidad': 100, 'ubicacion': 'Bodega A'}
        ]
        
        mock_cache = MagicMock()
        mock_cache.get.side_effect = Exception("Cache unavailable")
        mock_cache_client.return_value = mock_cache
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = microservice_data
        mock_get.return_value = mock_response
        
        # Act
        result = inventarios_service.get_inventarios_by_producto(producto_id)
        
        # Assert
        assert result['source'] == 'microservice'
        assert result['productoId'] == str(producto_id)
        mock_get.assert_called_once()
    
    # ==================== TESTS DE CREAR INVENTARIO ====================
    
    @patch('src.services.inventarios_service.requests.post')
    def test_crear_inventario_success(self, mock_post, inventarios_service):
        """Test: Crear inventario exitosamente."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': 100,
            'ubicacion': 'Bodega A - Estante 1',
            'usuario': 'admin'
        }
        
        expected_response = {
            'id': 'uuid-123',
            'productoId': 1,
            'cantidad': 100,
            'ubicacion': 'Bodega A - Estante 1',
            'usuarioCreacion': 'admin'
        }
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response
        
        # Act
        result = inventarios_service.crear_inventario(data)
        
        # Assert
        assert result['id'] == 'uuid-123'
        assert result['productoId'] == 1
        assert result['cantidad'] == 100
        mock_post.assert_called_once()
    
    @patch('src.services.inventarios_service.requests.post')
    def test_crear_inventario_producto_no_existe(self, mock_post, inventarios_service):
        """Test: Error al crear inventario con producto inexistente."""
        # Arrange
        data = {
            'productoId': 99999,
            'cantidad': 100,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'Recurso no encontrado',
            'mensaje': 'El producto con ID \'99999\' no existe'
        }
        mock_post.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(Exception):
            inventarios_service.crear_inventario(data)
    
    @patch('src.services.inventarios_service.requests.post')
    def test_crear_inventario_duplicado(self, mock_post, inventarios_service):
        """Test: Error al crear inventario duplicado."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': 100,
            'ubicacion': 'Bodega A - Estante 1',
            'usuario': 'admin'
        }
        
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.json.return_value = {
            'error': 'Conflicto',
            'mensaje': 'Ya existe un inventario para el producto \'1\' en la ubicación \'Bodega A - Estante 1\''
        }
        mock_post.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(Exception):
            inventarios_service.crear_inventario(data)
    
    # ==================== TESTS DE ACTUALIZAR INVENTARIO ====================
    
    @patch('src.services.inventarios_service.requests.put')
    def test_actualizar_inventario_success(self, mock_put, inventarios_service):
        """Test: Actualizar inventario exitosamente."""
        # Arrange
        inventario_id = 'uuid-123'
        data = {
            'cantidad': 150,
            'ubicacion': 'Bodega B - Estante 1',
            'usuario': 'admin'
        }
        
        expected_response = {
            'id': inventario_id,
            'productoId': 1,
            'cantidad': 150,
            'ubicacion': 'Bodega B - Estante 1',
            'usuarioActualizacion': 'admin'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_put.return_value = mock_response
        
        # Act
        result = inventarios_service.actualizar_inventario(inventario_id, data)
        
        # Assert
        assert result['id'] == inventario_id
        assert result['cantidad'] == 150
        assert result['ubicacion'] == 'Bodega B - Estante 1'
        mock_put.assert_called_once()
    
    @patch('src.services.inventarios_service.requests.put')
    def test_actualizar_inventario_no_existe(self, mock_put, inventarios_service):
        """Test: Error al actualizar inventario inexistente."""
        # Arrange
        inventario_id = 'uuid-inexistente'
        data = {'cantidad': 150}
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'Recurso no encontrado',
            'mensaje': f'Inventario con ID \'{inventario_id}\' no encontrado'
        }
        mock_put.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(Exception):
            inventarios_service.actualizar_inventario(inventario_id, data)
    
    # ==================== TESTS DE AJUSTAR CANTIDAD ====================
    
    @patch('src.services.inventarios_service.requests.post')
    def test_ajustar_cantidad_incremento_success(self, mock_post, inventarios_service):
        """Test: Incrementar cantidad exitosamente."""
        # Arrange
        inventario_id = 'uuid-123'
        data = {
            'ajuste': 50,
            'usuario': 'admin'
        }
        
        expected_response = {
            'id': inventario_id,
            'productoId': 1,
            'cantidad': 150,  # 100 + 50
            'ubicacion': 'Bodega A'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response
        
        # Act
        result = inventarios_service.ajustar_cantidad(inventario_id, data)
        
        # Assert
        assert result['cantidad'] == 150
        mock_post.assert_called_once()
    
    @patch('src.services.inventarios_service.requests.post')
    def test_ajustar_cantidad_decremento_success(self, mock_post, inventarios_service):
        """Test: Decrementar cantidad exitosamente."""
        # Arrange
        inventario_id = 'uuid-123'
        data = {
            'ajuste': -30,
            'usuario': 'admin'
        }
        
        expected_response = {
            'id': inventario_id,
            'productoId': 1,
            'cantidad': 70,  # 100 - 30
            'ubicacion': 'Bodega A'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response
        
        # Act
        result = inventarios_service.ajustar_cantidad(inventario_id, data)
        
        # Assert
        assert result['cantidad'] == 70
        mock_post.assert_called_once()
    
    @patch('src.services.inventarios_service.requests.post')
    def test_ajustar_cantidad_negativa(self, mock_post, inventarios_service):
        """Test: Error al ajustar cantidad resultando en negativo."""
        # Arrange
        inventario_id = 'uuid-123'
        data = {
            'ajuste': -150,  # Cantidad actual: 100
            'usuario': 'admin'
        }
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'Error de validación',
            'mensaje': 'El ajuste de -150 resultaría en una cantidad negativa (cantidad actual: 100)'
        }
        mock_post.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(Exception):
            inventarios_service.ajustar_cantidad(inventario_id, data)
    
    # ==================== TESTS DE ELIMINAR INVENTARIO ====================
    
    @patch('src.services.inventarios_service.requests.delete')
    def test_eliminar_inventario_success(self, mock_delete, inventarios_service):
        """Test: Eliminar inventario exitosamente."""
        # Arrange
        inventario_id = 'uuid-123'
        data = {'usuario': 'admin'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'mensaje': 'Inventario eliminado exitosamente'
        }
        mock_delete.return_value = mock_response
        
        # Act
        result = inventarios_service.eliminar_inventario(inventario_id, data)
        
        # Assert
        assert result['mensaje'] == 'Inventario eliminado exitosamente'
        mock_delete.assert_called_once()
    
    @patch('src.services.inventarios_service.requests.delete')
    def test_eliminar_inventario_no_existe(self, mock_delete, inventarios_service):
        """Test: Error al eliminar inventario inexistente."""
        # Arrange
        inventario_id = 'uuid-inexistente'
        data = {'usuario': 'admin'}
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'Recurso no encontrado',
            'mensaje': f'Inventario con ID \'{inventario_id}\' no encontrado'
        }
        mock_delete.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(Exception):
            inventarios_service.eliminar_inventario(inventario_id, data)
