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
    """Tests reducidos - 10 pruebas clave para cobertura óptima."""
    
    # ==================== 1. CREAR EXITOSO ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_crear_inventario_success(self, MockInventario, mock_db_session, mock_enqueue, mock_to_dict, sample_inventario_data):
        """Test 1: Crear inventario exitosamente con encolamiento."""
        mock_inventario = MagicMock()
        MockInventario.return_value = mock_inventario
        MockInventario.query.filter_by.return_value.first.return_value = None
        
        mock_to_dict.return_value = {
            'id': 'uuid-123',
            'productoId': 1,
            'cantidad': 100,
            'ubicacion': 'Bodega A',
            'usuarioCreacion': 'admin'
        }
        
        result = crear_inventario(sample_inventario_data)
        
        assert result['productoId'] == 1
        assert result['cantidad'] == 100
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_enqueue.assert_called_once()
    
    # ==================== 2. VALIDACIÓN CAMPOS OBLIGATORIOS ====================
    
    def test_crear_inventario_sin_campos(self):
        """Test 2: Error al crear sin campos obligatorios."""
        with pytest.raises(ValidationError, match="Faltan campos obligatorios"):
            crear_inventario({'cantidad': 100})
    
    # ==================== 3. VALIDACIÓN CANTIDAD ====================
    
    def test_crear_inventario_cantidad_negativa(self):
        """Test 3: Error con cantidad negativa."""
        data = {'productoId': 1, 'cantidad': -10, 'ubicacion': 'Bodega A'}
        with pytest.raises(ValidationError, match="positivo"):
            crear_inventario(data)
    
    # ==================== 4. DUPLICADOS ====================
    
    @patch('app.services.inventarios_service.Inventario')
    def test_crear_inventario_duplicado(self, MockInventario, sample_inventario_data):
        """Test 4: Error al intentar crear duplicado."""
        MockInventario.query.filter_by.return_value.first.return_value = MagicMock()
        with pytest.raises(ConflictError, match="Ya existe"):
            crear_inventario(sample_inventario_data)
    
    # ==================== 5. LISTAR CON FILTRO ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.Inventario')
    def test_listar_inventarios_filtro(self, MockInventario, mock_to_dict):
        """Test 5: Listar con filtro por producto."""
        mock_to_dict.return_value = {'id': '1', 'productoId': 1, 'cantidad': 100}
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [MagicMock()]
        MockInventario.query = mock_query
        
        result = listar_inventarios(producto_id=1)
        assert len(result) == 1
    
    # ==================== 6. OBTENER POR ID ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.Inventario')
    def test_obtener_por_id_success(self, MockInventario, mock_to_dict):
        """Test 6: Obtener por ID exitoso."""
        MockInventario.query.get.return_value = MagicMock()
        mock_to_dict.return_value = {'id': 'uuid-123', 'cantidad': 100}
        
        result = obtener_inventario_por_id('uuid-123')
        assert result['id'] == 'uuid-123'
    
    # ==================== 7. NOT FOUND ====================
    
    @patch('app.services.inventarios_service.Inventario')
    def test_obtener_no_existe(self, MockInventario):
        """Test 7: Error cuando inventario no existe."""
        MockInventario.query.get.return_value = None
        with pytest.raises(NotFoundError, match="no encontrado"):
            obtener_inventario_por_id('uuid-inexistente')
    
    # ==================== 8. ACTUALIZAR ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_actualizar_inventario(self, MockInventario, mock_db_session, mock_enqueue, mock_to_dict):
        """Test 8: Actualizar cantidad exitosamente."""
        mock_inventario = MagicMock()
        MockInventario.query.get.return_value = mock_inventario
        MockInventario.query.filter_by.return_value.first.return_value = None
        
        mock_to_dict.return_value = {'id': 'uuid-123', 'cantidad': 150}
        
        result = actualizar_inventario('uuid-123', {'cantidad': 150})
        assert result['cantidad'] == 150
        mock_enqueue.assert_called_once()
    
    # ==================== 9. AJUSTAR CANTIDAD ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_ajustar_cantidad(self, MockInventario, mock_db_session, mock_enqueue, mock_to_dict):
        """Test 9: Ajustar cantidad (incremento/decremento)."""
        mock_inventario = MagicMock()
        mock_inventario.cantidad = 100
        MockInventario.query.get.return_value = mock_inventario
        
        mock_to_dict.return_value = {'cantidad': 150}
        
        result = ajustar_cantidad('uuid-123', ajuste=50, usuario='admin')
        assert result['cantidad'] == 150
    
    # ==================== 10. ELIMINAR ====================
    
    @patch('app.services.inventarios_service._to_dict')
    @patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')
    @patch('app.services.inventarios_service.db.session')
    @patch('app.services.inventarios_service.Inventario')
    def test_eliminar_inventario(self, MockInventario, mock_db_session, mock_enqueue, mock_to_dict):
        """Test 10: Eliminar inventario exitosamente."""
        mock_inventario = MagicMock()
        MockInventario.query.get.return_value = mock_inventario
        
        mock_to_dict.return_value = {'id': 'uuid-123'}
        
        eliminar_inventario('uuid-123')
        mock_db_session.delete.assert_called_once()
        mock_enqueue.assert_called_once()


