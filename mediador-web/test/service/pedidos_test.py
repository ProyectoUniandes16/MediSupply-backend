import pytest
from unittest.mock import patch, MagicMock
import requests
from src.services.pedidos import listar_pedidos, PedidosServiceError
from flask import Flask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture(autouse=True)
def provide_app_context(app):
    with app.app_context():
        yield

# ==================== Tests para listar_pedidos ====================

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_exito(mock_get):
    """Test de listado exitoso de pedidos"""
    mock_response_data = {
        'data': [
            {'id': 'ped-1', 'cliente_id': 'cli-1', 'vendedor_id': 'ven-1', 'total': 100.0},
            {'id': 'ped-2', 'cliente_id': 'cli-2', 'vendedor_id': 'ven-2', 'total': 200.0}
        ]
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos()
        
        assert 'data' in result
        assert len(result['data']) == 2
        mock_get.assert_called_once_with(
            'http://localhost:5012/pedido',
            params={},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        mock_logger.info.assert_called_once()

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_con_filtros(mock_get):
    """Test de listado de pedidos con filtros"""
    mock_response_data = {
        'items': [
            {'id': 'ped-1', 'cliente_id': 'cli-123', 'vendedor_id': 'ven-456'}
        ],
        'total': 1
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos(cliente_id='cli-123', vendedor_id='ven-456')
        
        assert len(result['items']) == 1
        assert result['items'][0]['cliente_id'] == 'cli-123'
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert params['cliente_id'] == 'cli-123'
        assert params['vendedor_id'] == 'ven-456'

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_con_headers(mock_get):
    """Test de listado con headers personalizados"""
    mock_response_data = {'items': [], 'total': 0}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        custom_headers = {'Authorization': 'Bearer token456'}
        result = listar_pedidos(headers=custom_headers)
        
        assert result['total'] == 0
        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer token456'
        assert call_args[1]['headers']['Content-Type'] == 'application/json'

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_solo_cliente_id(mock_get):
    """Test de filtrado solo por cliente_id"""
    mock_response_data = {
        'items': [
            {'id': 'ped-10', 'cliente_id': 'cli-100'}
        ],
        'total': 1
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos(cliente_id='cli-100')
        
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert params['cliente_id'] == 'cli-100'
        assert 'vendedor_id' not in params

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_solo_vendedor_id(mock_get):
    """Test de filtrado solo por vendedor_id"""
    mock_response_data = {
        'items': [
            {'id': 'ped-20', 'vendedor_id': 'ven-200'}
        ],
        'total': 1
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos(vendedor_id='ven-200')
        
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert params['vendedor_id'] == 'ven-200'
        assert 'cliente_id' not in params

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_http_error(mock_get):
    """Test de error HTTP en listado de pedidos"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {'error': 'Error del servidor'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(PedidosServiceError) as excinfo:
            listar_pedidos()

        assert excinfo.value.status_code == 500
        mock_logger.error.assert_called_once()

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_connection_error(mock_get):
    """Test de error de conexión en listado de pedidos"""
    mock_get.side_effect = requests.exceptions.ConnectionError('Connection failed')

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(PedidosServiceError) as excinfo:
            listar_pedidos()

        assert excinfo.value.status_code == 503
        assert 'error de conexión' in excinfo.value.message.get('error').lower()
        mock_logger.error.assert_called_once()

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_timeout(mock_get):
    """Test de timeout en listado de pedidos"""
    mock_get.side_effect = requests.exceptions.Timeout('Request timeout')

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(PedidosServiceError) as excinfo:
            listar_pedidos()

        assert excinfo.value.status_code == 503

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_error_inesperado(mock_get):
    """Test de error inesperado en listado"""
    mock_get.side_effect = Exception('Error inesperado')

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(PedidosServiceError) as excinfo:
            listar_pedidos()

        assert excinfo.value.status_code == 500
        assert excinfo.value.message.get('codigo') == 'ERROR_INESPERADO'

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_lista_vacia(mock_get):
    """Test de listado vacío de pedidos"""
    mock_response_data = {'items': [], 'total': 0}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos()
        
        assert len(result['items']) == 0
        assert result['total'] == 0

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_respuesta_sin_json(mock_get):
    """Test cuando la respuesta de error HTTP no es JSON válido"""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = 'Bad Request'
    mock_response.json.side_effect = ValueError('Invalid JSON')
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(PedidosServiceError) as excinfo:
            listar_pedidos()

        assert excinfo.value.status_code == 400
        assert 'error' in excinfo.value.message
        assert excinfo.value.message['codigo'] == 'ERROR_HTTP'

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_con_variable_entorno(mock_get):
    """Test que verifica el uso de la variable de entorno PEDIDOS_URL"""
    mock_response_data = {'items': [], 'total': 0}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with patch.dict('os.environ', {'PEDIDOS_URL': 'http://custom-pedidos:9000'}):
            result = listar_pedidos()
            
            assert result['total'] == 0
            mock_get.assert_called_once_with(
                'http://custom-pedidos:9000/pedido',
                params={},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

