"""
Tests para las funciones de servicio de detalle de producto.
Prueba la comunicación con el microservicio de productos para obtener detalles.
"""
import re
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from src.services.productos import (
    ProductoServiceError,
    obtener_detalle_producto_externo,
    obtener_producto_por_sku_externo
)
import requests


@pytest.fixture
def app():
    """Fixture para crear una aplicación Flask de prueba"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


class TestObtenerDetalleProductoExterno:
    """Tests para obtener_detalle_producto_externo"""

    @patch('src.services.productos.requests.get')
    def test_obtener_detalle_exitoso(self, mock_get, app):
        """Debe retornar el detalle completo del producto cuando existe"""
        # Arrange
        producto_id = 1
        expected_data = {
            'id': 1,
            'nombre': 'Producto Test',
            'codigo_sku': 'TEST-001',
            'cantidad_disponible': 100,
            'precio_unitario': 50.00,
            'certificacion': {
                'id': 1,
                'nombre_archivo': 'cert.pdf'
            }
        }

        response = {
            'producto': expected_data
        }
        response['inventario'] = 'dato que debe ser removido'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response
        mock_get.return_value = mock_response

        # Act
        with app.app_context():
            result = obtener_detalle_producto_externo(producto_id)

        # Assert: la función devuelve el objeto tal cual recibido del microservicio
        # (se remueve la clave 'inventario' a nivel raíz), por lo que esperamos
        # {'producto': expected_data}
        assert result == {'producto': expected_data}
        from src.config.config import Config as CFG
        # El mock puede recibir llamadas adicionales (cache / inventarios).
        # Aseguramos que la primera llamada fue al endpoint de productos.
        first_call = mock_get.call_args_list[0]
        assert first_call[0][0] == f"{CFG.PRODUCTO_URL}/api/productos/1"

    @patch('src.services.productos.requests.get')
    def test_obtener_detalle_producto_no_encontrado(self, mock_get, app):
        """Debe lanzar ProductoServiceError 404 cuando el producto no existe"""
        # Arrange
        producto_id = 999
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_detalle_producto_externo(producto_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.message['codigo'] == 'PRODUCTO_NO_ENCONTRADO'
        assert 'no encontrado' in exc_info.value.message['error'].lower()

    @patch('src.services.productos.requests.get')
    def test_obtener_detalle_error_conexion(self, mock_get, app):
        """Debe lanzar ProductoServiceError 503 cuando hay error de conexión"""
        # Arrange
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')

        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_detalle_producto_externo(1)
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.message['codigo'] == 'ERROR_CONEXION'

    @patch('src.services.productos.requests.get')
    def test_obtener_detalle_error_500_del_microservicio(self, mock_get, app):
        """Debe propagar errores 500 del microservicio"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_response.json.return_value = {'error': 'Error interno', 'codigo': 'ERROR_DB'}
        mock_get.return_value = mock_response

        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_detalle_producto_externo(1)
        
        assert exc_info.value.status_code == 500


class TestObtenerProductoPorSkuExterno:
    """Tests para obtener_producto_por_sku_externo"""

    @patch('src.services.productos.requests.get')
    def test_obtener_por_sku_exitoso(self, mock_get, app):
        """Debe retornar el producto cuando el SKU existe"""
        # Arrange
        sku = 'TEST-001'
        expected_data = {
            'id': 1,
            'nombre': 'Producto Test',
            'codigo_sku': 'TEST-001',
            'cantidad_disponible': 50
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        # Act
        with app.app_context():
            result = obtener_producto_por_sku_externo(sku)

        # Assert
        assert result == expected_data
        from src.config.config import Config as CFG
        mock_get.assert_called_once_with(f"{CFG.PRODUCTO_URL}/api/productos/sku/TEST-001")

    @patch('src.services.productos.requests.get')
    def test_obtener_por_sku_no_encontrado(self, mock_get, app):
        """Debe lanzar ProductoServiceError 404 cuando el SKU no existe"""
        # Arrange
        sku = 'NO-EXISTE'
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_producto_por_sku_externo(sku)
        
        assert exc_info.value.status_code == 404
        assert 'NO-EXISTE' in exc_info.value.message['error']

    def test_obtener_por_sku_vacio(self, app):
        """Debe validar que el SKU no esté vacío"""
        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_producto_por_sku_externo('')
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.message['codigo'] == 'SKU_REQUERIDO'

    def test_obtener_por_sku_none(self, app):
        """Debe validar que el SKU no sea None"""
        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_producto_por_sku_externo(None)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.message['codigo'] == 'SKU_REQUERIDO'

    def test_obtener_por_sku_solo_espacios(self, app):
        """Debe validar que el SKU no sea solo espacios en blanco"""
        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                obtener_producto_por_sku_externo('   ')
        
        assert exc_info.value.status_code == 400