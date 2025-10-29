import pytest
from unittest.mock import patch, MagicMock
import requests
from src.services.vendedores import crear_vendedor_externo, listar_vendedores, VendedorServiceError
from flask import Flask

valid_vendedor_data = {
    'nombre': 'Juan',
    'apellidos': 'Perez',
    'correo': 'juan.perez@example.com',
    'telefono': '0987654321',
    'zona': 'Norte'
}

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture(autouse=True)
def provide_app_context(app):
    with app.app_context():
        yield

@patch('src.services.vendedores.requests.post')
def test_crear_vendedor_externo_exito(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 'vendedor1', 'nombre': 'Juan'}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = crear_vendedor_externo(valid_vendedor_data)
    assert result['nombre'] == 'Juan'
    # The service may call requests.post more than once (e.g. also calls auth service).
    # Ensure that among the calls there is one to the vendedores endpoint with expected args.
    calls = mock_post.call_args_list
    found = False
    for call_args in calls:
        args, kwargs = call_args
        if args and args[0] == 'http://localhost:5007/v1/vendedores' and kwargs.get('json') == valid_vendedor_data and kwargs.get('headers') == {'Content-Type': 'application/json'} and kwargs.get('timeout') == 10:
            found = True
            break
    assert found, f"Expected a post call to vendedores with payload {valid_vendedor_data}; calls: {calls}"

def test_crear_vendedor_externo_sin_datos():
    with pytest.raises(VendedorServiceError) as excinfo:
        crear_vendedor_externo(None)
    assert excinfo.value.status_code == 400

def test_crear_vendedor_externo_campos_faltantes():
    data = valid_vendedor_data.copy()
    del data['correo']
    with pytest.raises(VendedorServiceError) as excinfo:
        crear_vendedor_externo(data)
    assert excinfo.value.status_code == 400
    assert 'correo' in str(excinfo.value.message)

@patch('src.services.vendedores.requests.post')
def test_crear_vendedor_externo_http_error(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Datos inválidos'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_post.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            crear_vendedor_externo(valid_vendedor_data)

        mock_logger.error.assert_called_once()
        assert excinfo.value.status_code == 400
        assert 'error' in excinfo.value.message

@patch('src.services.vendedores.requests.post')
def test_crear_vendedor_externo_connection_error(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectionError('Connection failed')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            crear_vendedor_externo(valid_vendedor_data)

        mock_logger.error.assert_called_once()
        assert excinfo.value.status_code == 503
        assert 'error de conexión' in excinfo.value.message.get('error').lower()

# ==================== Tests para listar_vendedores ====================

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_exito(mock_get):
    """Test de listado exitoso de vendedores"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'items': [
            {'id': 'v1', 'nombre': 'Juan', 'apellidos': 'Perez', 'correo': 'juan@example.com'},
            {'id': 'v2', 'nombre': 'Maria', 'apellidos': 'Garcia', 'correo': 'maria@example.com'}
        ],
        'page': 1,
        'size': 10,
        'total': 2
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_vendedores(page=1, size=10)
        
        assert len(result['items']) == 2
        assert result['page'] == 1
        assert result['total'] == 2
        mock_get.assert_called_once_with(
            'http://localhost:5007/v1/vendedores',
            params={'page': 1, 'size': 10},
            timeout=10
        )
        mock_logger.info.assert_called_once()

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_con_filtros(mock_get):
    """Test de listado de vendedores con filtros de zona y estado"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'items': [
            {'id': 'v1', 'nombre': 'Juan', 'zona': 'Norte', 'estado': 'activo'}
        ],
        'page': 1,
        'size': 10,
        'total': 1
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_vendedores(zona='Norte', estado='activo', page=1, size=10)
        
        assert len(result['items']) == 1
        assert result['items'][0]['zona'] == 'Norte'
        assert result['items'][0]['estado'] == 'activo'
        mock_get.assert_called_once_with(
            'http://localhost:5007/v1/vendedores',
            params={'page': 1, 'size': 10, 'zona': 'Norte', 'estado': 'activo'},
            timeout=10
        )

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_paginacion(mock_get):
    """Test de paginación en listado de vendedores"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'items': [
            {'id': 'v3', 'nombre': 'Carlos'}
        ],
        'page': 2,
        'size': 5,
        'total': 15
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_vendedores(page=2, size=5)
        
        assert result['page'] == 2
        assert result['size'] == 5
        assert result['total'] == 15
        mock_get.assert_called_once_with(
            'http://localhost:5007/v1/vendedores',
            params={'page': 2, 'size': 5},
            timeout=10
        )

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_http_error(mock_get):
    """Test de error HTTP en listado de vendedores"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {'error': 'Error del servidor'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            listar_vendedores()

        mock_logger.error.assert_called_once()
        assert excinfo.value.status_code == 500

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_connection_error(mock_get):
    """Test de error de conexión en listado de vendedores"""
    mock_get.side_effect = requests.exceptions.ConnectionError('Connection failed')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            listar_vendedores()

        mock_logger.error.assert_called_once()
        assert excinfo.value.status_code == 503
        assert 'error de conexión' in excinfo.value.message.get('error').lower()

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_timeout(mock_get):
    """Test de timeout en listado de vendedores"""
    mock_get.side_effect = requests.exceptions.Timeout('Request timeout')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            listar_vendedores()

        assert excinfo.value.status_code == 503

@patch('src.services.vendedores.requests.get')
def test_listar_vendedores_lista_vacia(mock_get):
    """Test de listado vacío de vendedores"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'items': [],
        'page': 1,
        'size': 10,
        'total': 0
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        result = listar_vendedores()
        
        assert len(result['items']) == 0
        assert result['total'] == 0

# ==================== Tests para obtener_detalle_vendedor_externo ====================

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_exito(mock_get):
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
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = vendedor_mock
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        result = obtener_detalle_vendedor_externo('v123')
        
        assert result['id'] == 'v123'
        assert result['nombre'] == 'Juan'
        assert result['correo'] == 'juan.perez@example.com'
        assert result['zona'] == 'Norte'
        mock_get.assert_called_once_with('http://localhost:5007/v1/vendedores/v123')

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_no_encontrado_404(mock_get):
    """Test cuando el vendedor no existe (HTTP 404)"""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {'error': 'Vendedor no encontrado'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_detalle_vendedor_externo('v999')

        assert excinfo.value.status_code == 404
        mock_logger.error.assert_called_once()

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_error_conexion(mock_get):
    """Test de error de conexión con el microservicio"""
    mock_get.side_effect = requests.exceptions.ConnectionError('Connection failed')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_detalle_vendedor_externo('v123')

        assert excinfo.value.status_code == 503
        assert 'error de conexión' in excinfo.value.message.get('error').lower()
        assert excinfo.value.message.get('codigo') == 'ERROR_CONEXION'
        mock_logger.error.assert_called_once()

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_timeout(mock_get):
    """Test de timeout en la petición"""
    mock_get.side_effect = requests.exceptions.Timeout('Request timeout')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_detalle_vendedor_externo('v123')

        assert excinfo.value.status_code == 503
        assert excinfo.value.message.get('codigo') == 'ERROR_CONEXION'

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_error_http_500(mock_get):
    """Test de error HTTP 500 del microservicio"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {'error': 'Error interno del servidor', 'codigo': 'ERROR_INTERNO'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_detalle_vendedor_externo('v123')

        assert excinfo.value.status_code == 500
        mock_logger.error.assert_called_once()

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_error_inesperado(mock_get):
    """Test de error inesperado (Exception genérica)"""
    mock_get.side_effect = Exception('Error inesperado del sistema')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_detalle_vendedor_externo('v123')

        assert excinfo.value.status_code == 500
        assert 'error interno' in excinfo.value.message.get('error').lower()
        assert excinfo.value.message.get('codigo') == 'ERROR_INESPERADO'
        # Debe haber dos llamadas al logger: una para el error inesperado
        assert mock_logger.error.call_count >= 1

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_id_numerico(mock_get):
    """Test con ID numérico de vendedor"""
    vendedor_mock = {
        'id': 12345,
        'nombre': 'Maria',
        'apellidos': 'Lopez',
        'correo': 'maria@example.com'
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = vendedor_mock
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        result = obtener_detalle_vendedor_externo(12345)
        
        assert result['id'] == 12345
        assert result['nombre'] == 'Maria'
        mock_get.assert_called_once_with('http://localhost:5007/v1/vendedores/12345')

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_con_variable_entorno(mock_get):
    """Test que verifica el uso de la variable de entorno VENDEDORES_URL"""
    vendedor_mock = {'id': 'v1', 'nombre': 'Test'}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = vendedor_mock
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with patch.dict('os.environ', {'VENDEDORES_URL': 'http://custom-url:8080'}):
            from src.services.vendedores import obtener_detalle_vendedor_externo
            result = obtener_detalle_vendedor_externo('v1')
            
            assert result['id'] == 'v1'
            mock_get.assert_called_once_with('http://custom-url:8080/v1/vendedores/v1')

@patch('src.services.vendedores.requests.get')
def test_obtener_detalle_vendedor_externo_respuesta_completa(mock_get):
    """Test que valida que se retorna toda la información del vendedor"""
    vendedor_completo = {
        'id': 'vend-2025-001',
        'nombre': 'Carlos',
        'apellidos': 'Ramirez Gonzalez',
        'correo': 'carlos.ramirez@example.com',
        'telefono': '3109876543',
        'zona': 'Sur',
        'estado': 'activo',
        'fecha_creacion': '2025-01-20T15:45:00Z',
        'fecha_actualizacion': '2025-01-25T10:20:00Z',
        'ventas_realizadas': 150,
        'calificacion': 4.8
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = vendedor_completo
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        from src.services.vendedores import obtener_detalle_vendedor_externo
        result = obtener_detalle_vendedor_externo('vend-2025-001')
        
        # Verificar que todos los campos están presentes
        assert result['id'] == 'vend-2025-001'
        assert result['nombre'] == 'Carlos'
        assert result['apellidos'] == 'Ramirez Gonzalez'
        assert result['correo'] == 'carlos.ramirez@example.com'
        assert result['telefono'] == '3109876543'
        assert result['zona'] == 'Sur'
        assert result['estado'] == 'activo'
        assert result['ventas_realizadas'] == 150
        assert result['calificacion'] == 4.8
        assert 'fecha_creacion' in result
        assert 'fecha_actualizacion' in result
