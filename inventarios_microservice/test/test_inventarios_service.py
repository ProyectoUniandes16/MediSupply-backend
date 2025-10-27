import pytest
from unittest.mock import Mock, MagicMock, patch
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
    """Tests para el servicio de inventarios con mocks."""
    
    # ==================== TESTS DE CREAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_crear_inventario_success(self, MockInventario, mock_db_session, mock_enqueue, sample_inventario_data):
        """Test: Crear inventario exitosamente."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.id = 'uuid-123'
        mock_inventario.producto_id = 1
        mock_inventario.cantidad = 100
        mock_inventario.ubicacion = 'Bodega A - Estante 1'
        mock_inventario.usuario_creacion = 'admin'
        mock_inventario.to_dict.return_value = {
            'id': 'uuid-123',
            'productoId': 1,
            'cantidad': 100,
            'ubicacion': 'Bodega A - Estante 1',
            'usuarioCreacion': 'admin'
        }
        MockInventario.return_value = mock_inventario
        MockInventario.query.filter_by.return_value.first.return_value = None
        
        # Act
        result = crear_inventario(sample_inventario_data)
        
        # Assert
        assert result['productoId'] == 1
        assert result['cantidad'] == 100
        assert result['ubicacion'] == 'Bodega A - Estante 1'
        assert result['usuarioCreacion'] == 'admin'
        assert 'id' in result
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_enqueue.assert_called_once()
    
    def test_crear_inventario_sin_producto_id(self):
        """Test: Error al crear inventario sin productoId."""
        # Arrange
        data = {
            'cantidad': 100,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Faltan campos obligatorios.*productoId"):
            crear_inventario(data)
    
    def test_crear_inventario_sin_cantidad(self):
        """Test: Error al crear inventario sin cantidad."""
        # Arrange
        data = {
            'productoId': 1,
            'ubicacion': 'Bodega A',
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Faltan campos obligatorios.*cantidad"):
            crear_inventario(data)
    
    def test_crear_inventario_sin_ubicacion(self):
        """Test: Error al crear inventario sin ubicación."""
        # Arrange
        data = {
            'productoId': 1,
            'cantidad': 100,
            'usuario': 'admin'
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Faltan campos obligatorios.*ubicacion"):
            crear_inventario(data)
    
    def test_crear_inventario_cantidad_negativa(self):
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
    
    def test_crear_inventario_cantidad_cero(self):
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
    @patch('app.services.inventarios_service.Inventario')
    def test_crear_inventario_duplicado(self, MockInventario, mock_enqueue, sample_inventario_data):
        """Test: Error al crear inventario duplicado (mismo producto y ubicación)."""
        # Arrange
        mock_existing = MagicMock()
        MockInventario.query.filter_by.return_value.first.return_value = mock_existing
        
        # Act & Assert
        with pytest.raises(ConflictError, match="Ya existe.*inventario"):
            crear_inventario(sample_inventario_data)
    
    # ==================== TESTS DE LISTAR INVENTARIOS ====================
    
    @patch('app.services.inventarios_service.Inventario')
    def test_listar_inventarios_vacio(self, MockInventario):
        """Test: Listar inventarios cuando no hay ninguno."""
        # Arrange
        MockInventario.query.all.return_value = []
        
        # Act
        result = listar_inventarios()
        
        # Assert
        assert result == []
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.Inventario')
    def test_listar_inventarios_con_datos(self, MockInventario, mock_to_dict):
        """Test: Listar inventarios con datos."""
        # Arrange
        mock_inv1 = MagicMock()
        mock_inv2 = MagicMock()
        
        # Configurar mock_to_dict para retornar datos diferentes para cada inventario
        mock_to_dict.side_effect = [
            {'id': '1', 'productoId': 1, 'cantidad': 100},
            {'id': '2', 'productoId': 1, 'cantidad': 50}
        ]
        
        # Crear mock chain completo para query
        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [mock_inv1, mock_inv2]
        MockInventario.query = mock_query
        
        # Act
        result = listar_inventarios()
        
        # Assert
        assert len(result) == 2
        assert result[0]['productoId'] == 1
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.Inventario')
    def test_listar_inventarios_filtro_por_producto(self, MockInventario, mock_to_dict):
        """Test: Listar inventarios filtrados por producto."""
        # Arrange
        mock_inv = MagicMock()
        mock_to_dict.return_value = {'id': '1', 'productoId': 1, 'cantidad': 100}
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [mock_inv]
        MockInventario.query = mock_query
        
        # Act
        result = listar_inventarios(producto_id=1)
        
        # Assert
        assert len(result) == 1
        assert result[0]['productoId'] == 1
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.Inventario')
    def test_listar_inventarios_filtro_por_ubicacion(self, MockInventario, mock_to_dict):
        """Test: Listar inventarios filtrados por ubicación."""
        # Arrange
        mock_inv = MagicMock()
        mock_to_dict.return_value = {'id': '1', 'ubicacion': 'Bodega A - Estante 1'}
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [mock_inv]
        MockInventario.query = mock_query
        
        # Act
        result = listar_inventarios(ubicacion='Bodega A')
        
        # Assert
        assert len(result) == 1
        assert 'Bodega A' in result[0]['ubicacion']
    
    # ==================== TESTS DE OBTENER INVENTARIO ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.Inventario')
    def test_obtener_inventario_por_id_success(self, MockInventario, mock_to_dict):
        """Test: Obtener inventario por ID exitosamente."""
        # Arrange
        mock_inventario = MagicMock()
        MockInventario.query.get.return_value = mock_inventario
        
        mock_to_dict.return_value = {
            'id': 'uuid-123',
            'productoId': 1,
            'cantidad': 100
        }
        
        # Act
        result = obtener_inventario_por_id('uuid-123')
        
        # Assert
        assert result['id'] == 'uuid-123'
        assert result['cantidad'] == 100
        MockInventario.query.get.assert_called_once_with('uuid-123')
        mock_to_dict.assert_called_once_with(mock_inventario)
    
    @patch('app.services.inventarios_service.Inventario')
    def test_obtener_inventario_por_id_no_existe(self, MockInventario):
        """Test: Error al obtener inventario que no existe."""
        # Arrange
        MockInventario.query.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            obtener_inventario_por_id('uuid-inexistente')
    
    # ==================== TESTS DE ACTUALIZAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_actualizar_inventario_cantidad(self, MockInventario, mock_db_session, mock_enqueue):
        """Test: Actualizar cantidad de inventario."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.id = 'uuid-123'
        mock_inventario.cantidad = 100
        mock_inventario.to_dict.return_value = {
            'id': 'uuid-123',
            'cantidad': 150,
            'usuarioActualizacion': 'admin2'
        }
        MockInventario.query.get.return_value = mock_inventario
        MockInventario.query.filter_by.return_value.first.return_value = None
        
        # Act
        result = actualizar_inventario('uuid-123', {
            'cantidad': 150,
            'usuario': 'admin2'
        })
        
        # Assert
        assert result['cantidad'] == 150
        assert result['usuarioActualizacion'] == 'admin2'
        mock_db_session.commit.assert_called_once()
        mock_enqueue.assert_called_once()
    
    @patch('app.services.inventarios_service.Inventario')
    def test_actualizar_inventario_no_existe(self, MockInventario):
        """Test: Error al actualizar inventario que no existe."""
        # Arrange
        MockInventario.query.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            actualizar_inventario('uuid-inexistente', {'cantidad': 100})
    
    @patch('app.services.inventarios_service.Inventario')
    def test_actualizar_inventario_ubicacion_duplicada(self, MockInventario):
        """Test: Error al actualizar a ubicación que ya existe para ese producto."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.id = 'uuid-123'
        mock_inventario.producto_id = 1
        MockInventario.query.get.return_value = mock_inventario
        
        # Simular que ya existe otro inventario con la misma ubicación
        mock_existing = MagicMock()
        mock_existing.id = 'uuid-456'
        MockInventario.query.filter_by.return_value.first.return_value = mock_existing
        
        # Act & Assert
        with pytest.raises(ConflictError, match="Ya existe"):
            actualizar_inventario('uuid-123', {
                'ubicacion': 'Bodega A - Estante 1'
            })
    
    # ==================== TESTS DE AJUSTAR CANTIDAD ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_ajustar_cantidad_incremento(self, MockInventario, mock_db_session, mock_enqueue):
        """Test: Incrementar cantidad de inventario."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.id = 'uuid-123'
        mock_inventario.cantidad = 100
        mock_inventario.to_dict.return_value = {
            'id': 'uuid-123',
            'cantidad': 150
        }
        MockInventario.query.get.return_value = mock_inventario
        
        # Act
        result = ajustar_cantidad('uuid-123', ajuste=50, usuario='admin')
        
        # Assert
        assert result['cantidad'] == 150
        mock_db_session.commit.assert_called_once()
        mock_enqueue.assert_called_once()
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_ajustar_cantidad_decremento(self, MockInventario, mock_db_session, mock_enqueue):
        """Test: Decrementar cantidad de inventario."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.id = 'uuid-123'
        mock_inventario.cantidad = 100
        mock_inventario.to_dict.return_value = {
            'id': 'uuid-123',
            'cantidad': 70
        }
        MockInventario.query.get.return_value = mock_inventario
        
        # Act
        result = ajustar_cantidad('uuid-123', ajuste=-30, usuario='admin')
        
        # Assert
        assert result['cantidad'] == 70
        mock_db_session.commit.assert_called_once()
    
    @patch('app.services.inventarios_service.Inventario')
    def test_ajustar_cantidad_negativa(self, MockInventario):
        """Test: Error al ajustar cantidad resultando en negativo."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.cantidad = 100
        MockInventario.query.get.return_value = mock_inventario
        
        # Act & Assert
        with pytest.raises(ValidationError, match="cantidad negativa"):
            ajustar_cantidad('uuid-123', ajuste=-150, usuario='admin')
    
    @patch('app.services.inventarios_service.Inventario')
    def test_ajustar_cantidad_inventario_no_existe(self, MockInventario):
        """Test: Error al ajustar cantidad de inventario inexistente."""
        # Arrange
        MockInventario.query.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            ajustar_cantidad('uuid-inexistente', ajuste=10)
    
    # ==================== TESTS DE ELIMINAR INVENTARIO ====================
    
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_eliminar_inventario_success(self, MockInventario, mock_db_session, mock_enqueue):
        """Test: Eliminar inventario exitosamente."""
        # Arrange
        mock_inventario = MagicMock()
        mock_inventario.id = 'uuid-123'
        mock_inventario.to_dict.return_value = {'id': 'uuid-123', 'productoId': 1}
        MockInventario.query.get.return_value = mock_inventario
        
        # Act
        eliminar_inventario('uuid-123')
        
        # Assert
        mock_db_session.delete.assert_called_once_with(mock_inventario)
        mock_db_session.commit.assert_called_once()
        mock_enqueue.assert_called_once()
    
    @patch('app.services.inventarios_service.Inventario')
    def test_eliminar_inventario_no_existe(self, MockInventario):
        """Test: Error al eliminar inventario que no existe."""
        # Arrange
        MockInventario.query.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="no encontrado"):
            eliminar_inventario('uuid-inexistente')

