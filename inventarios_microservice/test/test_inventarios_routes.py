import pytest
import json
from unittest.mock import patch


class TestInventariosRoutes:
    """Tests para las rutas (endpoints) del microservicio de inventarios."""
    
    # ==================== TESTS DE HEALTH CHECK ====================
    
    def test_health_check(self, client):
        """Test: Endpoint de health check."""
        # Act
        response = client.get('/health')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data or 'estado' in data
    
    # ==================== TESTS DE CREAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_crear_inventario_endpoint_success(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint POST /api/inventarios - Crear inventario exitosamente."""
        # Act
        response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['productoId'] == 1
        assert data['cantidad'] == 100
        assert 'id' in data
    
    def test_crear_inventario_endpoint_sin_producto_id(self, client):
        """Test: Endpoint POST /api/inventarios - Error sin productoId."""
        # Arrange
        data = {
            'cantidad': 100,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act
        response = client.post(
            '/api/inventarios',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data or 'mensaje' in data
    
    def test_crear_inventario_endpoint_cantidad_negativa(self, client):
        """Test: Endpoint POST /api/inventarios - Error con cantidad negativa."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': -10,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act
        response = client.post(
            '/api/inventarios',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_crear_inventario_endpoint_duplicado(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint POST /api/inventarios - Error al crear duplicado."""
        # Arrange
        client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        
        # Act - Intentar crear duplicado
        response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 409
    
    # ==================== TESTS DE LISTAR INVENTARIOS ====================
    
    def test_listar_inventarios_endpoint_vacio(self, client):
        """Test: Endpoint GET /api/inventarios - Lista vacía."""
        # Act
        response = client.get('/api/inventarios')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_listar_inventarios_endpoint_con_datos(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint GET /api/inventarios - Lista con datos."""
        # Arrange
        client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        
        # Act
        response = client.get('/api/inventarios')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['productoId'] == 1
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_listar_inventarios_endpoint_filtro_producto(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint GET /api/inventarios?productoId=1 - Filtrar por producto."""
        # Arrange
        client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        
        # Act
        response = client.get('/api/inventarios?productoId=1')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
    
    # ==================== TESTS DE OBTENER INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_obtener_inventario_endpoint_success(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint GET /api/inventarios/{id} - Obtener exitosamente."""
        # Arrange
        create_response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        inventario_id = json.loads(create_response.data)['id']
        
        # Act
        response = client.get(f'/api/inventarios/{inventario_id}')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == inventario_id
    
    def test_obtener_inventario_endpoint_no_existe(self, client):
        """Test: Endpoint GET /api/inventarios/{id} - Inventario no existe."""
        # Act
        response = client.get('/api/inventarios/uuid-inexistente')
        
        # Assert
        assert response.status_code == 404
    
    # ==================== TESTS DE ACTUALIZAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_actualizar_inventario_endpoint_success(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint PUT /api/inventarios/{id} - Actualizar exitosamente."""
        # Arrange
        create_response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        inventario_id = json.loads(create_response.data)['id']
        
        # Act
        response = client.put(
            f'/api/inventarios/{inventario_id}',
            data=json.dumps({'cantidad': 150, 'usuario': 'admin2'}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['cantidad'] == 150
    
    def test_actualizar_inventario_endpoint_no_existe(self, client):
        """Test: Endpoint PUT /api/inventarios/{id} - Inventario no existe."""
        # Act
        response = client.put(
            '/api/inventarios/uuid-inexistente',
            data=json.dumps({'cantidad': 150}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 404
    
    # ==================== TESTS DE AJUSTAR CANTIDAD ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_ajustar_cantidad_endpoint_incremento(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint POST /api/inventarios/{id}/ajustar - Incrementar."""
        # Arrange
        create_response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        inventario_id = json.loads(create_response.data)['id']
        
        # Act
        response = client.post(
            f'/api/inventarios/{inventario_id}/ajustar',
            data=json.dumps({'ajuste': 50, 'usuario': 'admin'}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['cantidad'] == 150
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_ajustar_cantidad_endpoint_decremento(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint POST /api/inventarios/{id}/ajustar - Decrementar."""
        # Arrange
        create_response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        inventario_id = json.loads(create_response.data)['id']
        
        # Act
        response = client.post(
            f'/api/inventarios/{inventario_id}/ajustar',
            data=json.dumps({'ajuste': -30, 'usuario': 'admin'}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['cantidad'] == 70
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_ajustar_cantidad_endpoint_negativa(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint POST /api/inventarios/{id}/ajustar - Error cantidad negativa."""
        # Arrange
        create_response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        inventario_id = json.loads(create_response.data)['id']
        
        # Act
        response = client.post(
            f'/api/inventarios/{inventario_id}/ajustar',
            data=json.dumps({'ajuste': -150, 'usuario': 'admin'}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
    
    # ==================== TESTS DE ELIMINAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_eliminar_inventario_endpoint_success(self, mock_enqueue, client, sample_inventario_data):
        """Test: Endpoint DELETE /api/inventarios/{id} - Eliminar exitosamente."""
        # Arrange
        create_response = client.post(
            '/api/inventarios',
            data=json.dumps(sample_inventario_data),
            content_type='application/json'
        )
        inventario_id = json.loads(create_response.data)['id']
        
        # Act
        response = client.delete(f'/api/inventarios/{inventario_id}')
        
        # Assert
        assert response.status_code in [200, 204]
    
    def test_eliminar_inventario_endpoint_no_existe(self, client):
        """Test: Endpoint DELETE /api/inventarios/{id} - Inventario no existe."""
        # Act
        response = client.delete('/api/inventarios/uuid-inexistente')
        
        # Assert
        assert response.status_code == 404
