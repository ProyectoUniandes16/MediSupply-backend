from unittest.mock import MagicMock
import requests

from src.services.cache_client import CacheClient


def test_cache_client_behaviour(mocker):
    client = CacheClient('http://redis_service:5011')

    success = MagicMock(status_code=200)
    success.json.return_value = {'value': [{'cantidad': 2}]}

    not_found = MagicMock(status_code=404)

    error_resp = MagicMock(status_code=500)
    error_resp.json.return_value = {}

    mock_get = mocker.patch('src.services.cache_client.requests.get', return_value=success)

    data = client.get_inventarios_by_producto('123')
    assert data == [{'cantidad': 2}]

    mock_get.return_value = not_found
    assert client.get_inventarios_by_producto('123') is None

    mock_get.return_value = error_resp
    assert client.get_inventarios_by_producto('123') is None

    mock_get.side_effect = requests.Timeout()
    assert client.get_inventarios_by_producto('123') is None

    mock_get.side_effect = requests.RequestException('down')
    assert client.get_inventarios_by_producto('123') is None

    mock_get.side_effect = None
    mock_get.return_value = success
    assert client.is_available() is True

    mock_get.return_value = error_resp
    assert client.is_available() is False

    mock_get.side_effect = requests.RequestException('fail')
    assert client.is_available() is False


def test_cache_client_get_generic(mocker):
    """Test get_generic con diferentes escenarios."""
    client = CacheClient('http://redis:5011')
    mock_get = mocker.patch('src.services.cache_client.requests.get')
    
    # Cache HIT
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'value': {'test': 'data'}}
    result = client.get_generic('test_key')
    assert result == {'test': 'data'}
    
    # Cache MISS
    mock_get.return_value.status_code = 404
    result = client.get_generic('missing_key')
    assert result is None
    
    # Error status
    mock_get.return_value.status_code = 500
    result = client.get_generic('error_key')
    assert result is None
    
    # Timeout
    mock_get.side_effect = requests.Timeout()
    result = client.get_generic('timeout_key')
    assert result is None
    
    # RequestException
    mock_get.side_effect = requests.RequestException('error')
    result = client.get_generic('error_key')
    assert result is None
    
    # Exception genérica
    mock_get.side_effect = Exception('unexpected')
    result = client.get_generic('exception_key')
    assert result is None


def test_cache_client_set_generic(mocker):
    """Test set_generic con diferentes escenarios."""
    client = CacheClient('http://redis:5011')
    mock_post = mocker.patch('src.services.cache_client.requests.post')
    
    # Success con 200
    mock_post.return_value.status_code = 200
    result = client.set_generic('key1', {'data': 'value'}, ttl=300)
    assert result is True
    
    # Success con 201
    mock_post.return_value.status_code = 201
    result = client.set_generic('key2', [1, 2, 3])
    assert result is True
    
    # Error status
    mock_post.return_value.status_code = 500
    result = client.set_generic('key3', 'value')
    assert result is False
    
    # Timeout
    mock_post.side_effect = requests.Timeout()
    result = client.set_generic('key4', 'value')
    assert result is False
    
    # RequestException
    mock_post.side_effect = requests.RequestException('error')
    result = client.set_generic('key5', 'value')
    assert result is False
    
    # Exception genérica
    mock_post.side_effect = Exception('unexpected')
    result = client.set_generic('key6', 'value')
    assert result is False


def test_cache_client_init_url_cleanup():
    """Test que el constructor limpia las barras finales de la URL."""
    client = CacheClient('http://redis:5011///')
    assert client.redis_service_url == 'http://redis:5011'
    assert client.cache_endpoint == 'http://redis:5011/api/cache'


def test_cache_client_get_inventarios_exception(mocker):
    """Test manejo de excepción genérica en get_inventarios_by_producto."""
    client = CacheClient('http://redis:5011')
    mock_get = mocker.patch('src.services.cache_client.requests.get')
    mock_get.side_effect = Exception('unexpected error')
    
    result = client.get_inventarios_by_producto('123')
    assert result is None

