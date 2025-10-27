import pytest
from unittest.mock import Mock, patch
from app.services.inventarios_service import (
    crear_inventario,
    listar_inventarios,
    obtener_inventario_por_id,
    actualizar_inventario,
    eliminar_inventario,
    ajustar_cantidad
)
from app.services import NotFoundError, ConflictError, ValidationError
from app.models.inventario import Inventario
from app.models import db


class TestInventariosService:
    """Tests para el servicio de inventarios."""
    
    # ==================== TESTS DE CREAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_crear_inventario_success(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Crear inventario exitosamente."""
        # Act
        result = crear_inventario(sample_inventario_data)
        
        # Assert
        assert result['productoId'] == 1
        assert result['cantidad'] == 100
        assert result['ubicacion'] == 'Bodega A - Estante 1'
        assert result['usuarioCreacion'] == 'admin'
        assert 'id' in result
        
        # Verificar que se encoló el mensaje
        mock_enqueue.assert_called_once()
        
        # Verificar que se guardó en BD
        inventario = Inventario.query.filter_by(id=result['id']).first()
        assert inventario is not None
        assert inventario.cantidad == 100
    
    def test_crear_inventario_sin_producto_id(self, db_session):
        """Test: Error al crear inventario sin productoId."""
        # Arrange
        data = {
            'cantidad': 100,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="productoId.*requerido"):
            crear_inventario(data)
    
    def test_crear_inventario_sin_cantidad(self, db_session):
        """Test: Error al crear inventario sin cantidad."""
        # Arrange
        data = {
            'productoId': 1,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="cantidad.*requerido"):
            crear_inventario(data)
    
    def test_crear_inventario_sin_ubicacion(self, db_session):
        """Test: Error al crear inventario sin ubicación."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': 100,
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="ubicacion.*requerido"):
            crear_inventario(data)
    
    def test_crear_inventario_cantidad_negativa(self, db_session):
        """Test: Error al crear inventario con cantidad negativa."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': -10,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="positivo"):
            crear_inventario(data)
    
    def test_crear_inventario_cantidad_cero(self, db_session):
        """Test: Error al crear inventario con cantidad cero."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': 0,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="positivo"):
            crear_inventario(data)
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_crear_inventario_duplicado(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Error al crear inventario duplicado (mismo producto y ubicación)."""
        # Arrange - Crear primer inventario
        crear_inventario(sample_inventario_data)
        
        # Act & Assert - Intentar crear duplicado
        with pytest.raises(ConflictError, match="Ya existe.*inventario"):
            crear_inventario(sample_inventario_data)
    
    # ==================== TESTS DE LISTAR INVENTARIOS ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_listar_inventarios_vacio(self, mock_enqueue, db_session):
        """Test: Listar inventarios cuando no hay ninguno."""
        # Act
        result = listar_inventarios()
        
        # Assert
        assert result == []
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_listar_inventarios_con_datos(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Listar inventarios con datos."""
        # Arrange
        crear_inventario(sample_inventario_data)
        
        # Crear segundo inventario
        data2 = sample_inventario_data.copy()
        data2['ubicacion'] = 'Bodega B - Estante 1'
        crear_inventario(data2)
        
        # Act
        result = listar_inventarios()
        
        # Assert
        assert len(result) == 2
        assert result[0]['productoId'] == 1
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_listar_inventarios_filtro_por_producto(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Listar inventarios filtrados por producto."""
        # Arrange
        crear_inventario(sample_inventario_data)
        
        data2 = sample_inventario_data.copy()
        data2['productoId'] = 2
        data2['ubicacion'] = 'Bodega B'
        crear_inventario(data2)
        
        # Act
        result = listar_inventarios(producto_id=1)
        
        # Assert
        assert len(result) == 1
        assert result[0]['productoId'] == 1
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_listar_inventarios_filtro_por_ubicacion(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Listar inventarios filtrados por ubicación."""
        # Arrange
        crear_inventario(sample_inventario_data)
        
        data2 = sample_inventario_data.copy()
        data2['ubicacion'] = 'Bodega B - Estante 2'
        crear_inventario(data2)
        
        # Act
        result = listar_inventarios(ubicacion='Bodega A')
        
        # Assert
        assert len(result) == 1
        assert 'Bodega A' in result[0]['ubicacion']
    
    # ==================== TESTS DE OBTENER INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_obtener_inventario_por_id_success(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Obtener inventario por ID exitosamente."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act
        result = obtener_inventario_por_id(inventario_id)
        
        # Assert
        assert result['id'] == inventario_id
        assert result['cantidad'] == 100
    
    def test_obtener_inventario_por_id_no_existe(self, db_session):
        """Test: Error al obtener inventario que no existe."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            obtener_inventario_por_id('uuid-inexistente')
    
    # ==================== TESTS DE ACTUALIZAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_actualizar_inventario_cantidad(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Actualizar cantidad de inventario."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act
        result = actualizar_inventario(inventario_id, {
            'cantidad': 150,
            'usuario': 'admin2'
        })
        
        # Assert
        assert result['cantidad'] == 150
        assert result['usuarioActualizacion'] == 'admin2'
        assert mock_enqueue.call_count == 2  # create + update
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_actualizar_inventario_ubicacion(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Actualizar ubicación de inventario."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act
        result = actualizar_inventario(inventario_id, {
            'ubicacion': 'Bodega C - Estante 3',
            'usuario': 'admin'
        })
        
        # Assert
        assert result['ubicacion'] == 'Bodega C - Estante 3'
    
    def test_actualizar_inventario_no_existe(self, db_session):
        """Test: Error al actualizar inventario que no existe."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            actualizar_inventario('uuid-inexistente', {'cantidad': 100})
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_actualizar_inventario_ubicacion_duplicada(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Error al actualizar a ubicación que ya existe para ese producto."""
        # Arrange
        created1 = crear_inventario(sample_inventario_data)
        
        data2 = sample_inventario_data.copy()
        data2['ubicacion'] = 'Bodega B'
        created2 = crear_inventario(data2)
        
        # Act & Assert - Intentar actualizar inventario2 a la ubicación de inventario1
        with pytest.raises(ConflictError, match="Ya existe"):
            actualizar_inventario(created2['id'], {
                'ubicacion': 'Bodega A - Estante 1'
            })
    
    # ==================== TESTS DE AJUSTAR CANTIDAD ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_ajustar_cantidad_incremento(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Incrementar cantidad de inventario."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act
        result = ajustar_cantidad(inventario_id, ajuste=50, usuario='admin')
        
        # Assert
        assert result['cantidad'] == 150  # 100 + 50
        assert mock_enqueue.call_count == 2  # create + adjust
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_ajustar_cantidad_decremento(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Decrementar cantidad de inventario."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act
        result = ajustar_cantidad(inventario_id, ajuste=-30, usuario='admin')
        
        # Assert
        assert result['cantidad'] == 70  # 100 - 30
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_ajustar_cantidad_negativa(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Error al ajustar cantidad resultando en negativo."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act & Assert
        with pytest.raises(ValidationError, match="cantidad negativa"):
            ajustar_cantidad(inventario_id, ajuste=-150, usuario='admin')
    
    def test_ajustar_cantidad_inventario_no_existe(self, db_session):
        """Test: Error al ajustar cantidad de inventario inexistente."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            ajustar_cantidad('uuid-inexistente', ajuste=10)
    
    # ==================== TESTS DE ELIMINAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    def test_eliminar_inventario_success(self, mock_enqueue, db_session, sample_inventario_data):
        """Test: Eliminar inventario exitosamente."""
        # Arrange
        created = crear_inventario(sample_inventario_data)
        inventario_id = created['id']
        
        # Act
        eliminar_inventario(inventario_id)
        
        # Assert
        inventario = Inventario.query.get(inventario_id)
        assert inventario is None
        assert mock_enqueue.call_count == 2  # create + delete
    
    def test_eliminar_inventario_no_existe(self, db_session):
        """Test: Error al eliminar inventario que no existe."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            eliminar_inventario('uuid-inexistente')
