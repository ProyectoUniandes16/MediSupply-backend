"""Tests para CacheClient."""
import pytest
from unittest.mock import Mock, patch
from src.services.cache_client import CacheClient
from src import create_app
import requests


@pytest.fixture
def app():
    """Fixture para crear la aplicación Flask."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def cache_client():
    """Fixture para crear una instancia de CacheClient."""
    return CacheClient(
        base_url='http://localhost:5011',
        default_ttl=300,
        timeout=3
    )


@pytest.fixture
def mock_response():
    """Fixture para crear mock responses."""
    def _make_response(status_code, json_data=None):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        return response
    return _make_response


class TestCacheClientInit:
    """Tests para inicialización del cliente."""

    def test_init_con_parametros_default(self):
        """Verifica que se inicializa correctamente con parámetros por defecto."""
        client = CacheClient(base_url='http://redis:5011')
        assert client.base_url == 'http://redis:5011'
        assert client.cache_endpoint == 'http://redis:5011/api/cache'
        assert client.default_ttl == 300
        assert client.timeout == 3

    def test_init_con_parametros_personalizados(self):
        """Verifica que se inicializa con parámetros personalizados."""
        client = CacheClient(
            base_url='http://custom:8080/',
            default_ttl=600,
            timeout=5
        )
        assert client.base_url == 'http://custom:8080'
        assert client.default_ttl == 600
        assert client.timeout == 5

    def test_init_elimina_slash_final(self):
        """Verifica que se elimina el slash final de la URL."""
        client = CacheClient(base_url='http://redis:5011///')
        assert client.base_url == 'http://redis:5011'

    def test_from_app_config(self, app):
        """Verifica que se puede crear desde la configuración de Flask."""
        app.config['REDIS_SERVICE_URL'] = 'http://test:5011'
        app.config['CACHE_DEFAULT_TTL'] = 600
        
        with app.app_context():
            client = CacheClient.from_app_config()
            assert client.base_url == 'http://test:5011'
            assert client.default_ttl == 600

    def test_from_app_config_usa_defaults(self, app):
        """Verifica que usa valores por defecto si no están configurados."""
        # Eliminar las keys si existen
        app.config.pop('REDIS_SERVICE_URL', None)
        app.config.pop('CACHE_DEFAULT_TTL', None)
        
        with app.app_context():
            client = CacheClient.from_app_config()
            assert client.base_url == 'http://localhost:5011'
            assert client.default_ttl == 300


class TestCacheClientBuildKey:
    """Tests para construcción de keys."""

    def test_build_key_formato_correcto(self, cache_client):
        """Verifica que construye la key con el formato correcto."""
        key = cache_client._build_key('123')
        assert key == 'inventarios:producto:123'

    def test_encode_key_caracteres_especiales(self, cache_client):
        """Verifica que codifica caracteres especiales correctamente."""
        key = 'inventarios:producto:123'
        encoded = cache_client._encode_key(key)
        assert encoded == 'inventarios%3Aproducto%3A123'

    def test_encode_key_sin_caracteres_especiales(self, cache_client):
        """Verifica que no afecta strings sin caracteres especiales."""
        key = 'simple'
        encoded = cache_client._encode_key(key)
        assert encoded == 'simple'


class TestCacheClientGetInventarios:
    """Tests para obtener inventarios del cache."""

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_cache_hit(self, mock_get, cache_client, mock_response):
        """Verifica que retorna los datos cuando hay cache HIT."""
        inventarios = [{'id': '1', 'cantidad': 100}]
        mock_get.return_value = mock_response(200, {'value': inventarios})
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result == inventarios
        mock_get.assert_called_once_with(
            'http://localhost:5011/api/cache/inventarios%3Aproducto%3A123',
            timeout=3
        )

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_cache_miss(self, mock_get, cache_client, mock_response):
        """Verifica que retorna None cuando hay cache MISS (404)."""
        mock_get.return_value = mock_response(404)
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result is None

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_status_inesperado(self, mock_get, cache_client, mock_response):
        """Verifica que retorna None cuando hay status inesperado."""
        mock_get.return_value = mock_response(500)
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result is None

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_request_exception(self, mock_get, cache_client):
        """Verifica que maneja excepciones de requests correctamente."""
        mock_get.side_effect = requests.RequestException('Connection error')
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result is None

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_timeout(self, mock_get, cache_client):
        """Verifica que maneja timeout correctamente."""
        mock_get.side_effect = requests.Timeout('Timeout')
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result is None

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_value_es_none(self, mock_get, cache_client, mock_response):
        """Verifica que maneja correctamente cuando value es None."""
        mock_get.return_value = mock_response(200, {'value': None})
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result is None

    @patch('src.services.cache_client.requests.get')
    def test_get_inventarios_value_es_lista_vacia(self, mock_get, cache_client, mock_response):
        """Verifica que retorna lista vacía correctamente."""
        mock_get.return_value = mock_response(200, {'value': []})
        
        result = cache_client.get_inventarios_by_producto('123')
        
        assert result == []


class TestCacheClientSetInventarios:
    """Tests para guardar inventarios en cache."""

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_exitoso_status_200(self, mock_post, cache_client, mock_response):
        """Verifica que guarda correctamente con status 200."""
        mock_post.return_value = mock_response(200)
        inventarios = [{'id': '1', 'cantidad': 100}]
        
        result = cache_client.set_inventarios_by_producto('123', inventarios)
        
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json'] == {
            'key': 'inventarios:producto:123',
            'value': inventarios,
            'ttl': 300
        }

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_exitoso_status_201(self, mock_post, cache_client, mock_response):
        """Verifica que guarda correctamente con status 201."""
        mock_post.return_value = mock_response(201)
        inventarios = [{'id': '1', 'cantidad': 100}]
        
        result = cache_client.set_inventarios_by_producto('123', inventarios)
        
        assert result is True

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_con_ttl_personalizado(self, mock_post, cache_client, mock_response):
        """Verifica que usa TTL personalizado cuando se proporciona."""
        mock_post.return_value = mock_response(200)
        inventarios = [{'id': '1', 'cantidad': 100}]
        
        result = cache_client.set_inventarios_by_producto('123', inventarios, ttl=600)
        
        assert result is True
        call_args = mock_post.call_args
        assert call_args[1]['json']['ttl'] == 600

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_usa_default_ttl(self, mock_post, cache_client, mock_response):
        """Verifica que usa TTL por defecto cuando no se proporciona."""
        mock_post.return_value = mock_response(200)
        
        result = cache_client.set_inventarios_by_producto('123', [])
        
        assert result is True
        call_args = mock_post.call_args
        assert call_args[1]['json']['ttl'] == 300

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_error_status(self, mock_post, cache_client, mock_response):
        """Verifica que retorna False cuando hay error en status."""
        mock_post.return_value = mock_response(500)
        
        result = cache_client.set_inventarios_by_producto('123', [])
        
        assert result is False

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_request_exception(self, mock_post, cache_client):
        """Verifica que maneja excepciones de requests."""
        mock_post.side_effect = requests.RequestException('Error')
        
        result = cache_client.set_inventarios_by_producto('123', [])
        
        assert result is False

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_timeout(self, mock_post, cache_client):
        """Verifica que maneja timeout correctamente."""
        mock_post.side_effect = requests.Timeout('Timeout')
        
        result = cache_client.set_inventarios_by_producto('123', [])
        
        assert result is False

    @patch('src.services.cache_client.requests.post')
    def test_set_inventarios_con_lista_vacia(self, mock_post, cache_client, mock_response):
        """Verifica que puede guardar lista vacía."""
        mock_post.return_value = mock_response(200)
        
        result = cache_client.set_inventarios_by_producto('123', [])
        
        assert result is True
        call_args = mock_post.call_args
        assert call_args[1]['json']['value'] == []


class TestCacheClientDeleteProductoCache:
    """Tests para eliminar cache de producto."""

    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_exitoso(self, mock_delete, cache_client, mock_response):
        """Verifica que elimina correctamente cuando status es 200."""
        mock_delete.return_value = mock_response(200)
        
        result = cache_client.delete_producto_cache('123')
        
        assert result is True
        mock_delete.assert_called_once_with(
            'http://localhost:5011/api/cache/inventarios%3Aproducto%3A123',
            timeout=3
        )

    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_no_encontrado(self, mock_delete, cache_client, mock_response):
        """Verifica que retorna False cuando no encuentra la key (404)."""
        mock_delete.return_value = mock_response(404)
        
        result = cache_client.delete_producto_cache('123')
        
        assert result is False

    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_error_servidor(self, mock_delete, cache_client, mock_response):
        """Verifica que retorna False cuando hay error del servidor."""
        mock_delete.return_value = mock_response(500)
        
        result = cache_client.delete_producto_cache('123')
        
        assert result is False

    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_request_exception(self, mock_delete, cache_client):
        """Verifica que maneja excepciones de requests."""
        mock_delete.side_effect = requests.RequestException('Error')
        
        result = cache_client.delete_producto_cache('123')
        
        assert result is False

    @patch('src.services.cache_client.requests.delete')
    def test_delete_cache_timeout(self, mock_delete, cache_client):
        """Verifica que maneja timeout correctamente."""
        mock_delete.side_effect = requests.Timeout('Timeout')
        
        result = cache_client.delete_producto_cache('123')
        
        assert result is False


class TestCacheClientIsAvailable:
    """Tests para verificar disponibilidad del servicio."""

    @patch('src.services.cache_client.requests.get')
    def test_is_available_servicio_disponible(self, mock_get, cache_client, mock_response):
        """Verifica que retorna True cuando el servicio está disponible."""
        mock_get.return_value = mock_response(200)
        
        result = cache_client.is_available()
        
        assert result is True
        mock_get.assert_called_once_with(
            'http://localhost:5011/health',
            timeout=2
        )

    @patch('src.services.cache_client.requests.get')
    def test_is_available_servicio_no_saludable(self, mock_get, cache_client, mock_response):
        """Verifica que retorna False cuando health retorna status diferente de 200."""
        mock_get.return_value = mock_response(500)
        
        result = cache_client.is_available()
        
        assert result is False

    @patch('src.services.cache_client.requests.get')
    def test_is_available_request_exception(self, mock_get, cache_client):
        """Verifica que retorna False cuando hay excepción de requests."""
        mock_get.side_effect = requests.RequestException('Connection refused')
        
        result = cache_client.is_available()
        
        assert result is False

    @patch('src.services.cache_client.requests.get')
    def test_is_available_timeout(self, mock_get, cache_client):
        """Verifica que retorna False cuando hay timeout."""
        mock_get.side_effect = requests.Timeout('Timeout')
        
        result = cache_client.is_available()
        
        assert result is False

    @patch('src.services.cache_client.requests.get')
    def test_is_available_usa_timeout_corto(self, mock_get, cache_client, mock_response):
        """Verifica que usa timeout de 2 segundos (más corto que otras operaciones)."""
        mock_get.return_value = mock_response(200)
        
        cache_client.is_available()
        
        call_args = mock_get.call_args
        assert call_args[1]['timeout'] == 2
