"""
Tests para los endpoints de detalle de producto en el blueprint.
Prueba los endpoints GET para obtener detalle por ID, SKU y descarga de certificación.
"""
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.producto import producto_bp
from src.services.productos import ProductoServiceError
from unittest.mock import patch, Mock
import io


@pytest.fixture
def app():
    """Fixture para crear la aplicación Flask de prueba"""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-key'
    app.config['TESTING'] = True
    jwt = JWTManager(app)
    app.register_blueprint(producto_bp)
    return app


@pytest.fixture
def client(app):
    """Fixture para el cliente de pruebas"""
    return app.test_client()


@pytest.fixture
def token(app):
    """Fixture para generar un token JWT válido"""
    with app.app_context():
        return create_access_token(identity='test-user')


@pytest.fixture
def auth_headers(token):
    """Fixture para headers con autenticación"""
    return {'Authorization': f'Bearer {token}'}


class TestObtenerDetalleProducto:
    """Tests para el endpoint GET /producto/{id}"""

    def test_obtener_detalle_exitoso(self, client, auth_headers, mocker):
        """Debe retornar el detalle del producto cuando existe"""
        # Arrange
        producto_id = 1
        expected_data = {
            'id': 1,
            'nombre': 'Paracetamol',
            'codigo_sku': 'MED-001',
            'cantidad_disponible': 100,
            'precio_unitario': 25.50,
            'certificacion': {
                'id': 1,
                'nombre_archivo': 'cert.pdf'
            }
        }
        
        mocker.patch(
            'src.blueprints.producto.obtener_detalle_producto_externo',
            return_value=expected_data
        )

        # Act
        response = client.get(f'/producto/{producto_id}', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data'] == expected_data

    def test_obtener_detalle_sin_autenticacion(self, client):
        """Debe retornar 401 si no hay token JWT"""
        # Act
        response = client.get('/producto/1')

        # Assert
        assert response.status_code == 401

    def test_obtener_detalle_producto_no_encontrado(self, client, auth_headers, mocker):
        """Debe retornar 404 cuando el producto no existe"""
        # Arrange
        error = ProductoServiceError({
            'error': 'Producto con ID 999 no encontrado',
            'codigo': 'PRODUCTO_NO_ENCONTRADO'
        }, 404)
        
        mocker.patch(
            'src.blueprints.producto.obtener_detalle_producto_externo',
            side_effect=error
        )

        # Act
        response = client.get('/producto/999', headers=auth_headers)

        # Assert
        assert response.status_code == 404
        data = response.get_json()
        assert data['codigo'] == 'PRODUCTO_NO_ENCONTRADO'

    def test_obtener_detalle_error_conexion(self, client, auth_headers, mocker):
        """Debe retornar 503 cuando hay error de conexión con el microservicio"""
        # Arrange
        error = ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
        
        mocker.patch(
            'src.blueprints.producto.obtener_detalle_producto_externo',
            side_effect=error
        )

        # Act
        response = client.get('/producto/1', headers=auth_headers)

        # Assert
        assert response.status_code == 503
        data = response.get_json()
        assert data['codigo'] == 'ERROR_CONEXION'

    def test_obtener_detalle_error_inesperado(self, client, auth_headers, mocker):
        """Debe retornar 500 cuando hay un error inesperado"""
        # Arrange
        mocker.patch(
            'src.blueprints.producto.obtener_detalle_producto_externo',
            side_effect=Exception('Error inesperado')
        )

        # Act
        response = client.get('/producto/1', headers=auth_headers)

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data['codigo'] == 'ERROR_INESPERADO'


class TestObtenerProductoPorSku:
    """Tests para el endpoint GET /producto/sku/{sku}"""

    def test_obtener_por_sku_exitoso(self, client, auth_headers, mocker):
        """Debe retornar el producto cuando el SKU existe"""
        # Arrange
        sku = 'MED-001'
        expected_data = {
            'id': 1,
            'nombre': 'Paracetamol',
            'codigo_sku': 'MED-001',
            'cantidad_disponible': 50
        }
        
        mocker.patch(
            'src.blueprints.producto.obtener_producto_por_sku_externo',
            return_value=expected_data
        )

        # Act
        response = client.get(f'/producto/sku/{sku}', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data']['codigo_sku'] == sku

    def test_obtener_por_sku_no_encontrado(self, client, auth_headers, mocker):
        """Debe retornar 404 cuando el SKU no existe"""
        # Arrange
        sku = 'NO-EXISTE'
        error = ProductoServiceError({
            'error': f'Producto con SKU {sku} no encontrado',
            'codigo': 'PRODUCTO_NO_ENCONTRADO'
        }, 404)
        
        mocker.patch(
            'src.blueprints.producto.obtener_producto_por_sku_externo',
            side_effect=error
        )

        # Act
        response = client.get(f'/producto/sku/{sku}', headers=auth_headers)

        # Assert
        assert response.status_code == 404
        data = response.get_json()
        assert 'NO-EXISTE' in data['error']

    def test_obtener_por_sku_sin_autenticacion(self, client):
        """Debe retornar 401 si no hay token JWT"""
        # Act
        response = client.get('/producto/sku/TEST-001')

        # Assert
        assert response.status_code == 401

    def test_obtener_por_sku_con_caracteres_especiales(self, client, auth_headers, mocker):
        """Debe manejar SKUs con caracteres especiales como guiones y guiones bajos"""
        # Arrange
        sku = 'MED-001_ABC'  # SKU con guión y guión bajo (caracteres válidos comunes)
        expected_data = {
            'id': 1,
            'codigo_sku': sku
        }
        
        mocker.patch(
            'src.blueprints.producto.obtener_producto_por_sku_externo',
            return_value=expected_data
        )

        # Act
        response = client.get(f'/producto/sku/{sku}', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['codigo_sku'] == sku


class TestDescargarCertificacion:
    """Tests para el endpoint GET /producto/{id}/certificacion"""

    def test_descargar_certificacion_exitoso(self, client, auth_headers, mocker):
        """Debe retornar el archivo cuando existe"""
        # Arrange
        producto_id = 1
        file_content = b'%PDF-1.4 fake pdf content'
        filename = 'certificado_producto_1.pdf'
        mimetype = 'application/pdf'
        
        mocker.patch(
            'src.blueprints.producto.descargar_certificacion_producto_externo',
            return_value=(file_content, filename, mimetype)
        )

        # Act
        response = client.get(f'/producto/{producto_id}/certificacion', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.data == file_content
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        assert filename in response.headers.get('Content-Disposition', '')

    def test_descargar_certificacion_no_encontrada(self, client, auth_headers, mocker):
        """Debe retornar 404 cuando no hay certificación"""
        # Arrange
        error = ProductoServiceError({
            'error': 'No hay certificación disponible para este producto',
            'codigo': 'CERTIFICACION_NO_ENCONTRADA'
        }, 404)
        
        mocker.patch(
            'src.blueprints.producto.descargar_certificacion_producto_externo',
            side_effect=error
        )

        # Act
        response = client.get('/producto/1/certificacion', headers=auth_headers)

        # Assert
        assert response.status_code == 404
        data = response.get_json()
        assert data['codigo'] == 'CERTIFICACION_NO_ENCONTRADA'

    def test_descargar_certificacion_sin_autenticacion(self, client):
        """Debe retornar 401 si no hay token JWT"""
        # Act
        response = client.get('/producto/1/certificacion')

        # Assert
        assert response.status_code == 401

    def test_descargar_certificacion_error_servicio(self, client, auth_headers, mocker):
        """Debe retornar 503 cuando hay error en el microservicio"""
        # Arrange
        error = ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
        
        mocker.patch(
            'src.blueprints.producto.descargar_certificacion_producto_externo',
            side_effect=error
        )

        # Act
        response = client.get('/producto/1/certificacion', headers=auth_headers)

        # Assert
        assert response.status_code == 503

    def test_descargar_certificacion_diferentes_tipos_archivo(self, client, auth_headers, mocker):
        """Debe manejar diferentes tipos de archivos (PDF, PNG, etc.)"""
        # Arrange
        file_content = b'PNG fake content'
        filename = 'certificado.png'
        mimetype = 'image/png'
        
        mocker.patch(
            'src.blueprints.producto.descargar_certificacion_producto_externo',
            return_value=(file_content, filename, mimetype)
        )

        # Act
        response = client.get('/producto/1/certificacion', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.content_type == 'image/png'
        assert 'certificado.png' in response.headers.get('Content-Disposition', '')

    def test_descargar_certificacion_error_inesperado(self, client, auth_headers, mocker):
        """Debe retornar 500 cuando hay un error inesperado"""
        # Arrange
        mocker.patch(
            'src.blueprints.producto.descargar_certificacion_producto_externo',
            side_effect=Exception('Error inesperado')
        )

        # Act
        response = client.get('/producto/1/certificacion', headers=auth_headers)

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data['codigo'] == 'ERROR_INESPERADO'
