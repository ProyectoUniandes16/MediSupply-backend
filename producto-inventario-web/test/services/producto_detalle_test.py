"""
Tests para las funciones de servicio de detalle de producto.
Prueba la comunicación con el microservicio de productos para obtener detalles.
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from src.services.productos import (
    ProductoServiceError,
    obtener_detalle_producto_externo,
    obtener_producto_por_sku_externo,
    descargar_certificacion_producto_externo
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
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        # Act
        with app.app_context():
            result = obtener_detalle_producto_externo(producto_id)

        # Assert
        assert result == expected_data
        mock_get.assert_called_once_with('http://localhost:5008/api/productos/1')

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
        mock_get.assert_called_once_with('http://localhost:5008/api/productos/sku/TEST-001')

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


class TestDescargarCertificacionProductoExterno:
    """Tests para descargar_certificacion_producto_externo"""

    @patch('src.services.productos.requests.get')
    def test_descargar_certificacion_exitoso(self, mock_get, app):
        """Debe retornar el contenido del archivo cuando existe"""
        # Arrange
        producto_id = 1
        file_content = b'%PDF-1.4 fake pdf content'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = file_content
        mock_response.headers = {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="certificado_producto_1.pdf"'
        }
        mock_get.return_value = mock_response

        # Act
        with app.app_context():
            content, filename, mimetype = descargar_certificacion_producto_externo(producto_id)

        # Assert
        assert content == file_content
        assert filename == 'certificado_producto_1.pdf'
        assert mimetype == 'application/pdf'
        mock_get.assert_called_once_with(
            'http://localhost:5008/api/productos/1/certificacion/descargar',
            stream=True
        )

    @patch('src.services.productos.requests.get')
    def test_descargar_certificacion_no_encontrada(self, mock_get, app):
        """Debe lanzar ProductoServiceError 404 cuando no hay certificación"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                descargar_certificacion_producto_externo(1)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.message['codigo'] == 'CERTIFICACION_NO_ENCONTRADA'

    @patch('src.services.productos.requests.get')
    def test_descargar_certificacion_sin_content_disposition(self, mock_get, app):
        """Debe usar un nombre por defecto si no hay Content-Disposition"""
        # Arrange
        file_content = b'pdf content'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = file_content
        mock_response.headers = {
            'Content-Type': 'application/pdf'
        }
        mock_get.return_value = mock_response

        # Act
        with app.app_context():
            content, filename, mimetype = descargar_certificacion_producto_externo(1)

        # Assert
        assert filename == 'certificacion.pdf'  # nombre por defecto

    @patch('src.services.productos.requests.get')
    def test_descargar_certificacion_error_conexion(self, mock_get, app):
        """Debe lanzar ProductoServiceError 503 cuando hay error de conexión"""
        # Arrange
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')

        # Act & Assert
        with app.app_context():
            with pytest.raises(ProductoServiceError) as exc_info:
                descargar_certificacion_producto_externo(1)
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.message['codigo'] == 'ERROR_CONEXION'

    @patch('src.services.productos.requests.get')
    def test_descargar_certificacion_diferentes_tipos_mime(self, mock_get, app):
        """Debe manejar diferentes tipos MIME correctamente"""
        # Arrange
        file_content = b'image content'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = file_content
        mock_response.headers = {
            'Content-Type': 'image/png',
            'Content-Disposition': 'attachment; filename="certificado.png"'
        }
        mock_get.return_value = mock_response

        # Act
        with app.app_context():
            content, filename, mimetype = descargar_certificacion_producto_externo(1)

        # Assert
        assert mimetype == 'image/png'
        assert filename == 'certificado.png'
