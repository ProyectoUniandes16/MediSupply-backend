import pytest
from unittest.mock import patch, MagicMock
import requests

from src.services.vendedores import obtener_clientes_de_vendedor, VendedorServiceError


def test_obtener_clientes_de_vendedor_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'data': [{'cliente_id': 1}]}

    with patch('src.services.vendedores.requests.get', return_value=mock_response) as mock_get:
        result = obtener_clientes_de_vendedor('v@e.com')

    assert result == {'data': [{'cliente_id': 1}]}
    mock_get.assert_called_once()


def test_obtener_clientes_de_vendedor_non_200():
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch('src.services.vendedores.requests.get', return_value=mock_response):
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_clientes_de_vendedor('v@e.com')

    assert excinfo.value.status_code == 500


def test_obtener_clientes_de_vendedor_request_exception():
    with patch('src.services.vendedores.requests.get', side_effect=requests.exceptions.RequestException('fail')):
        with pytest.raises(requests.exceptions.RequestException):
            obtener_clientes_de_vendedor('v@e.com')
