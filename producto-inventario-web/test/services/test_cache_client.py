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
