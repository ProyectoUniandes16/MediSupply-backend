import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from src.blueprints.producto import producto_bp
from src.services.productos import ProductoServiceError
from flask_jwt_extended import create_access_token
from unittest.mock import patch

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-key'
    jwt = JWTManager(app)
    app.register_blueprint(producto_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def token(app):
    # Genera un access token de prueba (mockea usuario 'test-user')
    with app.test_request_context():
        from flask_jwt_extended import create_access_token
        return create_access_token(identity='test-user')

def test_consultar_productos_endpoint():
    """GET /productos debe devolver lo que retorne get_productos_con_inventarios"""
    from src import create_app

    app = create_app()
    client = app.test_client()

    # Preparar token válido (usa la configuración de la app)
    with app.app_context():
        access_token = create_access_token(identity='test-user')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    expected = {
        'data': [{'id': 1, 'nombre': 'Producto A', 'inventarios': [], 'totalInventario': 0, 'inventariosSource': 'cache'}],
        'total': 1,
        'source': 'cache'
    }

    # Parchear la función que agrega inventarios EN EL MÓDULO DEL BLUEPRINT
    with patch('src.blueprints.producto.get_productos_con_inventarios', return_value=expected) as mock_agregado:
        resp = client.get('/producto', headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data == expected
    mock_agregado.assert_called()


def test_consultar_productos_service_error(mocker, client, token):
    """Si get_productos_con_inventarios lanza InventarioServiceError, el blueprint debe propagar su contenido y status."""
    from src.services.inventarios import InventarioServiceError
    err = InventarioServiceError({'error': 'servicio caido', 'codigo': 'ERR_SERV'}, 503)
    mocker.patch('src.blueprints.producto.get_productos_con_inventarios', side_effect=err)

    resp = client.get('/producto', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 503
    assert resp.get_json() == {'error': 'servicio caido', 'codigo': 'ERR_SERV'}


def test_consultar_productos_unexpected_exception(mocker, client, token):
    """Si ocurre una excepción no controlada, retornar 500 con codigo ERROR_INESPERADO."""
    mocker.patch('src.blueprints.producto.get_productos_con_inventarios', side_effect=Exception('boom'))

    resp = client.get('/producto', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 500
    data = resp.get_json()
    assert data.get('codigo') == 'ERROR_INESPERADO'
