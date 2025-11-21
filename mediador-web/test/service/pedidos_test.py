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
    """Test de listado exitoso de pedidos con enriquecimiento de datos de cliente"""
    # Mock de respuesta del servicio de pedidos
    mock_pedidos_response = {
        'data': [
            {'id': 'ped-1', 'cliente_id': 'cli-1', 'vendedor_id': 'ven-1', 'total': 100.0},
            {'id': 'ped-2', 'cliente_id': 'cli-2', 'vendedor_id': 'ven-2', 'total': 200.0}
        ]
    }
    
    # Mock de respuestas del servicio de clientes
    mock_cliente1_response = {
        'data': {
            'id': 'cli-1',
            'zona': 'Norte',
            'ubicacion': 'Calle 123'
        }
    }
    
    mock_cliente2_response = {
        'data': {
            'id': 'cli-2',
            'zona': 'Sur',
            'ubicacion': 'Carrera 456'
        }
    }
    
    # Configurar el mock para que retorne diferentes respuestas según la URL
    def side_effect_get(*args, **kwargs):
        url = args[0]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        if '/pedido' in url:
            mock_response.json.return_value = mock_pedidos_response
        elif '/cliente/cli-1' in url:
            mock_response.json.return_value = mock_cliente1_response
        elif '/cliente/cli-2' in url:
            mock_response.json.return_value = mock_cliente2_response
        
        return mock_response
    
    mock_get.side_effect = side_effect_get

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos()
        
        assert 'data' in result
        assert len(result['data']) == 2
        # Verificar que los pedidos tienen información del cliente enriquecida
        assert result['data'][0]['cliente_zona'] == 'Norte'
        assert result['data'][0]['cliente_ubicacion'] == 'Calle 123'
        assert result['data'][1]['cliente_zona'] == 'Sur'
        assert result['data'][1]['cliente_ubicacion'] == 'Carrera 456'
        
        # Verificar que se hicieron las 3 llamadas (1 pedidos + 2 clientes)
        assert mock_get.call_count == 3
        mock_logger.info.assert_called_once()

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_con_filtros(mock_get):
    """Test de listado de pedidos con filtros"""
    mock_pedidos_response = {
        'data': [
            {'id': 'ped-1', 'cliente_id': 'cli-123', 'vendedor_id': 'ven-456'}
        ]
    }
    
    mock_cliente_response = {
        'data': {
            'id': 'cli-123',
            'zona': 'Centro',
            'ubicacion': 'Calle Principal'
        }
    }
    
    def side_effect_get(*args, **kwargs):
        url = args[0]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        if '/pedido' in url:
            mock_response.json.return_value = mock_pedidos_response
        elif '/cliente/cli-123' in url:
            mock_response.json.return_value = mock_cliente_response
        
        return mock_response
    
    mock_get.side_effect = side_effect_get

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos(cliente_id='cli-123', vendedor_id='ven-456')
        
        assert len(result['data']) == 1
        assert result['data'][0]['cliente_id'] == 'cli-123'
        assert result['data'][0]['cliente_zona'] == 'Centro'

@patch('src.services.pedidos.requests.get')
def test_listar_pedidos_con_headers(mock_get):
    """Test de listado con headers personalizados"""
    mock_response_data = {'data': []}
    
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
        
        assert len(result['data']) == 0
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
    mock_response_data = {'data': []}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.pedidos.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_pedidos()
        
        assert len(result['data']) == 0

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
    mock_response_data = {'data': []}
    
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
            
            assert len(result['data']) == 0
            mock_get.assert_called_once_with(
                'http://custom-pedidos:9000/pedido',
                params={},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

