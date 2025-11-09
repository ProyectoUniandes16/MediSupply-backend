"""
Tests unitarios para el servicio de pedidos.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.pedidos import obtener_pedidos_vendedor, PedidosServiceError


class TestObtenerPedidosVendedor:
    """Tests para obtener_pedidos_vendedor"""
    
    @patch('src.services.pedidos.requests.get')
    def test_obtener_pedidos_sin_filtro_fecha(self, mock_get):
        """Test: obtener pedidos sin filtrar por mes/año"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 1,
                    'vendedor_id': 'v123',
                    'cliente_id': 100,
                    'total': 1500.50,
                    'fecha_pedido': '2025-01-15T10:30:00',
                    'estado': 'completado'
                },
                {
                    'id': 2,
                    'vendedor_id': 'v123',
                    'cliente_id': 101,
                    'total': 2000.00,
                    'fecha_pedido': '2025-02-20T14:00:00',
                    'estado': 'completado'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Act
        resultado = obtener_pedidos_vendedor('v123')
        
        # Assert
        assert len(resultado) == 2
        assert resultado[0]['id'] == 1
        assert resultado[1]['id'] == 2
        mock_get.assert_called_once()
    
    @patch('src.services.pedidos.requests.get')
    def test_obtener_pedidos_con_filtro_fecha(self, mock_get):
        """Test: obtener pedidos filtrados por mes y año"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 1,
                    'vendedor_id': 'v123',
                    'cliente_id': 100,
                    'total': 1500.50,
                    'fecha_pedido': '2025-01-15T10:30:00',
                    'estado': 'completado'
                },
                {
                    'id': 2,
                    'vendedor_id': 'v123',
                    'cliente_id': 101,
                    'total': 2000.00,
                    'fecha_pedido': '2025-02-20T14:00:00',
                    'estado': 'completado'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Act - filtrar solo enero 2025
        resultado = obtener_pedidos_vendedor('v123', mes=1, anio=2025)
        
        # Assert - solo debe retornar el pedido de enero
        assert len(resultado) == 1
        assert resultado[0]['id'] == 1
    
    @patch('src.services.pedidos.requests.get')
    def test_obtener_pedidos_error_conexion(self, mock_get):
        """Test: error de conexión con microservicio"""
        # Arrange
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection failed')
        
        # Act & Assert
        with pytest.raises(PedidosServiceError) as exc:
            obtener_pedidos_vendedor('v123')
        
        assert exc.value.status_code == 503
        assert 'ERROR_CONEXION' in str(exc.value.message)
    
    @patch('src.services.pedidos.requests.get')
    def test_obtener_pedidos_sin_datos(self, mock_get):
        """Test: obtener pedidos cuando no hay datos"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        # Act
        resultado = obtener_pedidos_vendedor('v123', mes=1, anio=2025)
        
        # Assert
        assert len(resultado) == 0
        assert isinstance(resultado, list)
