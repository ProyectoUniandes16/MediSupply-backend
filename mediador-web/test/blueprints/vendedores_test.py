import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.vendedores import vendedores_bp
from src.services.vendedores import VendedorServiceError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    JWTManager(app)
    app.register_blueprint(vendedores_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity='user123')

@patch('src.blueprints.vendedores.crear_vendedor_externo')
def test_crear_vendedor_exito(mock_crear_vendedor, client, access_token):
    mock_crear_vendedor.return_value = {'id': 'vendedor1', 'nombre': 'Vendedor Test'}

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/vendedor', json={'nombre': 'Vendedor Test'}, headers=headers)

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['id'] == 'vendedor1'

@patch('src.blueprints.vendedores.crear_vendedor_externo')
def test_crear_vendedor_error_controlado(mock_crear_vendedor, client, access_token):
    error = VendedorServiceError({'error': 'Error en datos'}, 400)
    mock_crear_vendedor.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/vendedor', json={'nombre': 'Vendedor Test'}, headers=headers)

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data

@patch('src.blueprints.vendedores.crear_vendedor_externo')
def test_crear_vendedor_error_inesperado(mock_crear_vendedor, client, access_token, app):
    mock_crear_vendedor.side_effect = Exception('Error inesperado')
    mock_logger = MagicMock()

    with app.app_context():
        with patch('src.blueprints.vendedores.current_app') as mock_current_app:
            mock_current_app.logger = mock_logger

            headers = {'Authorization': f'Bearer {access_token}'}
            response = client.post('/vendedor', json={'nombre': 'Vendedor Test'}, headers=headers)

            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data and 'interno' in json_data['error'].lower()
            mock_logger.error.assert_called_once()

def test_crear_vendedor_sin_token(client):
    # Sin autorización debe responder 401
    response = client.post('/vendedor', json={'nombre': 'Vendedor Test'})
    assert response.status_code == 401

# ==================== Tests para GET /vendedor ====================

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_exito(mock_listar, client, access_token):
    """Test de listado exitoso de vendedores"""
    mock_listar.return_value = {
        'items': [
            {'id': 'v1', 'nombre': 'Juan', 'apellidos': 'Perez'},
            {'id': 'v2', 'nombre': 'Maria', 'apellidos': 'Garcia'}
        ],
        'page': 1,
        'size': 10,
        'total': 2
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 2
    assert json_data['total'] == 2
    mock_listar.assert_called_once_with(zona=None, estado=None, nombre=None, page=1, size=10)

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_con_filtros(mock_listar, client, access_token):
    """Test de listado de vendedores con filtros"""
    mock_listar.return_value = {
        'items': [
            {'id': 'v1', 'nombre': 'Juan', 'zona': 'Norte', 'estado': 'activo'}
        ],
        'page': 1,
        'size': 10,
        'total': 1
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor?zona=Norte&estado=activo', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 1
    mock_listar.assert_called_once_with(zona='Norte', estado='activo', nombre=None, page=1, size=10)

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_con_paginacion(mock_listar, client, access_token):
    """Test de paginación en listado de vendedores"""
    mock_listar.return_value = {
        'items': [{'id': 'v3', 'nombre': 'Carlos'}],
        'page': 2,
        'size': 5,
        'total': 15
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor?page=2&size=5', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['page'] == 2
    assert json_data['size'] == 5
    mock_listar.assert_called_once_with(zona=None, estado=None, nombre=None, page=2, size=5)

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_pagina_invalida(mock_listar, client, access_token):
    """Test de validación de número de página inválido"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor?page=0', headers=headers)

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    assert 'página' in json_data['error'].lower()
    mock_listar.assert_not_called()

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_size_invalido(mock_listar, client, access_token):
    """Test de validación de tamaño de página inválido"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # size = 0
    response = client.get('/vendedor?size=0', headers=headers)
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    
    # size > 100
    response = client.get('/vendedor?size=101', headers=headers)
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    
    mock_listar.assert_not_called()

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_parametros_no_numericos(mock_listar, client, access_token):
    """Test de error con parámetros no numéricos"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor?page=abc', headers=headers)

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    assert 'números enteros' in json_data['message'].lower()
    mock_listar.assert_not_called()

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_error_servicio(mock_listar, client, access_token):
    """Test de error controlado desde el servicio"""
    error = VendedorServiceError({'error': 'Error del microservicio'}, 503)
    mock_listar.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor', headers=headers)

    assert response.status_code == 503
    json_data = response.get_json()
    assert 'error' in json_data

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_error_inesperado(mock_listar, client, access_token, app):
    """Test de error inesperado en listado"""
    mock_listar.side_effect = Exception('Error inesperado')
    mock_logger = MagicMock()

    with app.app_context():
        with patch('src.blueprints.vendedores.current_app') as mock_current_app:
            mock_current_app.logger = mock_logger

            headers = {'Authorization': f'Bearer {access_token}'}
            response = client.get('/vendedor', headers=headers)

            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data
            assert 'interno' in json_data['error'].lower()
            mock_logger.error.assert_called_once()

def test_obtener_vendedores_sin_token(client):
    """Test de acceso sin token de autenticación"""
    response = client.get('/vendedor')
    assert response.status_code == 401

@patch('src.blueprints.vendedores.listar_vendedores')
def test_obtener_vendedores_lista_vacia(mock_listar, client, access_token):
    """Test de listado vacío de vendedores"""
    mock_listar.return_value = {
        'items': [],
        'page': 1,
        'size': 10,
        'total': 0
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 0
    assert json_data['total'] == 0

# ==================== Tests para GET /vendedor/<vendedor_id> ====================

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_exito(mock_obtener_detalle, client, access_token):
    """Test de obtención exitosa del detalle de un vendedor"""
    vendedor_mock = {
        'id': 'v123',
        'nombre': 'Juan',
        'apellidos': 'Perez Garcia',
        'correo': 'juan.perez@example.com',
        'telefono': '3001234567',
        'zona': 'Norte',
        'estado': 'activo',
        'fecha_creacion': '2025-01-15T10:30:00Z'
    }
    mock_obtener_detalle.return_value = vendedor_mock

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor/v123', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert 'data' in json_data
    assert json_data['data']['id'] == 'v123'
    assert json_data['data']['nombre'] == 'Juan'
    assert json_data['data']['correo'] == 'juan.perez@example.com'
    mock_obtener_detalle.assert_called_once_with('v123')

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_no_encontrado(mock_obtener_detalle, client, access_token):
    """Test cuando el vendedor no existe"""
    error = VendedorServiceError({
        'error': 'Vendedor con ID v999 no encontrado',
        'codigo': 'VENDEDOR_NO_ENCONTRADO'
    }, 404)
    mock_obtener_detalle.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor/v999', headers=headers)

    assert response.status_code == 404
    json_data = response.get_json()
    assert 'error' in json_data
    assert 'no encontrado' in json_data['error'].lower()
    assert json_data['codigo'] == 'VENDEDOR_NO_ENCONTRADO'
    mock_obtener_detalle.assert_called_once_with('v999')

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_error_conexion(mock_obtener_detalle, client, access_token):
    """Test de error de conexión con el microservicio"""
    error = VendedorServiceError({
        'error': 'Error de conexión con el microservicio de vendedores',
        'codigo': 'ERROR_CONEXION'
    }, 503)
    mock_obtener_detalle.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor/v123', headers=headers)

    assert response.status_code == 503
    json_data = response.get_json()
    assert 'error' in json_data
    assert json_data['codigo'] == 'ERROR_CONEXION'
    mock_obtener_detalle.assert_called_once_with('v123')

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_error_inesperado(mock_obtener_detalle, client, access_token, app):
    """Test de error inesperado al obtener detalle"""
    mock_obtener_detalle.side_effect = Exception('Error inesperado del sistema')
    mock_logger = MagicMock()

    with app.app_context():
        with patch('src.blueprints.vendedores.current_app') as mock_current_app:
            mock_current_app.logger = mock_logger

            headers = {'Authorization': f'Bearer {access_token}'}
            response = client.get('/vendedor/v123', headers=headers)

            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data
            assert 'interno' in json_data['error'].lower()
            assert json_data['codigo'] == 'ERROR_INESPERADO'
            mock_logger.error.assert_called_once()
            # Verificar que el log contiene el ID del vendedor
            call_args = mock_logger.error.call_args[0][0]
            assert 'v123' in call_args

def test_obtener_detalle_vendedor_sin_token(client):
    """Test de acceso sin token de autenticación"""
    response = client.get('/vendedor/v123')
    assert response.status_code == 401

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_id_numerico(mock_obtener_detalle, client, access_token):
    """Test con ID numérico de vendedor"""
    vendedor_mock = {
        'id': '12345',
        'nombre': 'Maria',
        'apellidos': 'Lopez',
        'correo': 'maria@example.com'
    }
    mock_obtener_detalle.return_value = vendedor_mock

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor/12345', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['data']['id'] == '12345'
    mock_obtener_detalle.assert_called_once_with('12345')

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_id_con_caracteres_especiales(mock_obtener_detalle, client, access_token):
    """Test con ID que contiene caracteres especiales"""
    vendedor_mock = {
        'id': 'vend-2025-001',
        'nombre': 'Carlos',
        'apellidos': 'Ramirez'
    }
    mock_obtener_detalle.return_value = vendedor_mock

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor/vend-2025-001', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['data']['id'] == 'vend-2025-001'
    mock_obtener_detalle.assert_called_once_with('vend-2025-001')

@patch('src.blueprints.vendedores.obtener_detalle_vendedor_externo')
def test_obtener_detalle_vendedor_error_servicio_generico(mock_obtener_detalle, client, access_token):
    """Test de error genérico del servicio"""
    error = VendedorServiceError({
        'error': 'Error interno del microservicio',
        'codigo': 'ERROR_INTERNO'
    }, 500)
    mock_obtener_detalle.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/vendedor/v123', headers=headers)

    assert response.status_code == 500
    json_data = response.get_json()
    assert 'error' in json_data
    mock_obtener_detalle.assert_called_once_with('v123')
