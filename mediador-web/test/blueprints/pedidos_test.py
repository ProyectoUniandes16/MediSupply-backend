import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.pedidos import pedidos_bp
from src.services.pedidos import PedidosServiceError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    JWTManager(app)
    app.register_blueprint(pedidos_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity='user123')

# ==================== Tests para GET /pedido ====================

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_exito(mock_listar, client, access_token):
    """Test de listado exitoso de pedidos"""
    mock_listar.return_value = {
        'items': [
            {'id': 'ped-1', 'cliente_id': 'cli-1', 'vendedor_id': 'ven-1'},
            {'id': 'ped-2', 'cliente_id': 'cli-2', 'vendedor_id': 'ven-2'}
        ],
        'total': 2
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 2
    assert json_data['total'] == 2
    
    # Verificar llamada con parámetros por defecto
    call_args = mock_listar.call_args
    assert call_args[1]['vendedor_id'] is None
    assert call_args[1]['cliente_id'] is None

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_con_filtro_cliente(mock_listar, client, access_token):
    """Test de listado de pedidos con filtro por cliente"""
    mock_listar.return_value = {
        'items': [
            {'id': 'ped-1', 'cliente_id': 'cli-123', 'vendedor_id': 'ven-456'}
        ],
        'total': 1
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido?cliente_id=cli-123', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 1
    
    # Verificar que se pasó el filtro de cliente_id
    call_args = mock_listar.call_args
    assert call_args[1]['cliente_id'] == 'cli-123'

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_con_filtro_vendedor(mock_listar, client, access_token):
    """Test de listado de pedidos con filtro por vendedor"""
    mock_listar.return_value = {
        'items': [
            {'id': 'ped-2', 'cliente_id': 'cli-789', 'vendedor_id': 'ven-999'}
        ],
        'total': 1
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido?vendedor_id=ven-999', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['total'] == 1
    
    # Verificar que se pasó el filtro de vendedor_id
    call_args = mock_listar.call_args
    assert call_args[1]['vendedor_id'] == 'ven-999'

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_con_ambos_filtros(mock_listar, client, access_token):
    """Test de listado con filtros por cliente y vendedor"""
    mock_listar.return_value = {
        'items': [
            {'id': 'ped-10', 'cliente_id': 'cli-100', 'vendedor_id': 'ven-200'}
        ],
        'total': 1
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido?cliente_id=cli-100&vendedor_id=ven-200', headers=headers)

    assert response.status_code == 200
    
    # Verificar que se pasaron ambos filtros
    call_args = mock_listar.call_args
    assert call_args[1]['cliente_id'] == 'cli-100'
    assert call_args[1]['vendedor_id'] == 'ven-200'

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_error_servicio(mock_listar, client, access_token):
    """Test de error controlado desde el servicio"""
    error = PedidosServiceError({'error': 'Error del microservicio'}, 503)
    mock_listar.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido', headers=headers)

    assert response.status_code == 503
    json_data = response.get_json()
    assert 'error' in json_data

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_error_inesperado(mock_listar, client, access_token, app):
    """Test de error inesperado en listado"""
    mock_listar.side_effect = Exception('Error inesperado')
    mock_logger = MagicMock()

    with app.app_context():
        with patch('src.blueprints.pedidos.current_app') as mock_current_app:
            mock_current_app.logger = mock_logger

            headers = {'Authorization': f'Bearer {access_token}'}
            response = client.get('/pedido', headers=headers)

            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data
            assert 'interno' in json_data['error'].lower()
            mock_logger.error.assert_called_once()

def test_listar_pedidos_sin_token(client):
    """Test de acceso sin token de autenticación"""
    response = client.get('/pedido')
    assert response.status_code == 401

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_lista_vacia(mock_listar, client, access_token):
    """Test de listado vacío de pedidos"""
    mock_listar.return_value = {
        'items': [],
        'total': 0
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 0
    assert json_data['total'] == 0

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_pasa_headers_autorizacion(mock_listar, client, access_token):
    """Test que verifica que se pasan correctamente los headers de autorización"""
    mock_listar.return_value = {'items': [], 'total': 0}

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido', headers=headers)

    assert response.status_code == 200
    
    # Verificar que se pasaron los headers al servicio
    call_args = mock_listar.call_args
    assert 'headers' in call_args[1]
    passed_headers = call_args[1]['headers']
    assert 'Authorization' in passed_headers
    assert passed_headers['Authorization'] == f'Bearer {access_token}'

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_sin_filtros(mock_listar, client, access_token):
    """Test de listado sin filtros (todos los pedidos)"""
    mock_listar.return_value = {
        'items': [
            {'id': 'ped-1'},
            {'id': 'ped-2'},
            {'id': 'ped-3'}
        ],
        'total': 3
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['total'] == 3
    
    # Verificar que no se pasaron filtros
    call_args = mock_listar.call_args
    assert call_args[1]['cliente_id'] is None
    assert call_args[1]['vendedor_id'] is None

@patch('src.blueprints.pedidos.listar_pedidos')
def test_listar_pedidos_con_filtro_zona(mock_listar, client, access_token):
    """Test de listado de pedidos con filtro por zona del cliente"""
    mock_listar.return_value = {
        'data': [
            {'id': 'ped-1', 'cliente_id': 'cli-1', 'vendedor_id': 'ven-1'},
            {'id': 'ped-2', 'cliente_id': 'cli-2', 'vendedor_id': 'ven-2'}
        ]
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido?zona=bogota', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['data']) == 2
    
    # Verificar que se pasó el filtro de zona
    call_args = mock_listar.call_args
    assert call_args[1]['zona'] == 'bogota'

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_filtrado_zona_integracion(mock_requests_get, client, access_token):
    """Test de integración del filtrado por zona con llamadas reales a microservicios"""
    # Mock de respuesta del microservicio de pedidos
    pedidos_response = MagicMock()
    pedidos_response.json.return_value = {
        'data': [
            {'id': 'ped-1', 'cliente_id': 1, 'vendedor_id': 'ven-1', 'fecha_pedido': '2025-01-15T10:00:00'},
            {'id': 'ped-2', 'cliente_id': 2, 'vendedor_id': 'ven-2', 'fecha_pedido': '2025-01-16T11:00:00'},
            {'id': 'ped-3', 'cliente_id': 3, 'vendedor_id': 'ven-3', 'fecha_pedido': '2025-01-17T12:00:00'}
        ]
    }
    pedidos_response.raise_for_status.return_value = None

    # Mock de respuestas del microservicio de clientes
    cliente1_response = MagicMock()
    cliente1_response.json.return_value = {'data': {'zona': 'bogota'}}
    cliente1_response.raise_for_status.return_value = None

    cliente2_response = MagicMock()
    cliente2_response.json.return_value = {'data': {'zona': 'bogota'}}
    cliente2_response.raise_for_status.return_value = None

    cliente3_response = MagicMock()
    cliente3_response.json.return_value = {'data': {'zona': 'lima'}}  # Zona diferente
    cliente3_response.raise_for_status.return_value = None

    # Configurar el mock para devolver diferentes respuestas según la URL
    def mock_get_side_effect(*args, **kwargs):
        url = args[0]
        if 'pedido' in url:
            return pedidos_response
        elif 'cliente/1' in url:
            return cliente1_response
        elif 'cliente/2' in url:
            return cliente2_response
        elif 'cliente/3' in url:
            return cliente3_response
        return MagicMock()

    mock_requests_get.side_effect = mock_get_side_effect

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/pedido?zona=bogota', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    
    # Debería devolver solo 2 pedidos (cliente 1 y 2 están en bogota, cliente 3 en lima)
    assert len(json_data['data']) == 2
    assert json_data['data'][0]['cliente_id'] == 1
    assert json_data['data'][1]['cliente_id'] == 2
    
    # Verificar que se hicieron las llamadas correctas
    assert mock_requests_get.call_count == 4  # 1 para pedidos + 3 para clientes

