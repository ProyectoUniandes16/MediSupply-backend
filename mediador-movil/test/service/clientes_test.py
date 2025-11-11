import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import requests

from src.services.clientes import crear_cliente_externo, ClienteServiceError
from src.services.auth import AuthServiceError


@pytest.fixture
def app():
    a = Flask(__name__)
    a.config['JWT_SECRET_KEY'] = 'secret'
    return a


def minimal_cliente():
    return {
        'nombre': 'Empresa X',
        'tipo': 'SAS',
        'zona': 'Ciudad de México',
        'nit': '12345',
        'nombre_contacto': 'Contacto',
        'correo_contacto': 'c@x.com',
        'telefono_contacto': '3001234',
        'direccion': 'Calle 1',
        'cargo_contacto': 'Gerente',
        'correo_empresa': 'empresa@x.com'
    }


def test_crear_cliente_no_datos():
    with pytest.raises(ClienteServiceError) as excinfo:
        crear_cliente_externo(None)
    assert excinfo.value.status_code == 400
    assert 'No se proporcionaron datos' in excinfo.value.message['error']


def test_crear_cliente_missing_fields():
    datos = minimal_cliente()
    del datos['correo_contacto']
    with pytest.raises(ClienteServiceError) as excinfo:
        crear_cliente_externo(datos)
    assert excinfo.value.status_code == 400
    assert 'Campos faltantes' in excinfo.value.message['error']


@patch('src.services.clientes.requests.post')
@patch('src.services.clientes.requests.patch')
@patch('src.services.clientes.register_user')
def test_crear_cliente_success(mock_register, mock_patch, mock_post, app):
    cliente_resp = {'id': 'c1', 'nombre': 'Empresa X'}

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = cliente_resp
    mock_post.return_value = mock_response

    mock_register.return_value = {'data': {'user': {'id': 99}}}

    mock_patch_resp = MagicMock()
    mock_patch_resp.raise_for_status = MagicMock()
    mock_patch_resp.json.return_value = {'ok': True}
    mock_patch.return_value = mock_patch_resp

    with app.app_context():
        result = crear_cliente_externo(minimal_cliente())

    assert result == cliente_resp
    mock_post.assert_called_once()
    mock_register.assert_called_once()
    mock_patch.assert_called_once()


@patch('src.services.clientes.requests.post')
@patch('src.services.clientes.register_user')
def test_crear_cliente_register_user_fails_but_returns(mock_register, mock_post, app):
    cliente_resp = {'id': 'c1', 'nombre': 'Empresa X'}

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = cliente_resp
    mock_post.return_value = mock_response

    # register_user raises AuthServiceError but should be swallowed
    mock_register.side_effect = AuthServiceError({'error': 'algo'}, 400)

    with app.app_context():
        result = crear_cliente_externo(minimal_cliente())

    assert result == cliente_resp
    mock_register.assert_called_once()


@patch('src.services.clientes.requests.post')
def test_crear_cliente_http_error(mock_post, app):
    mock_resp = MagicMock()
    mock_resp.text = 'error'
    mock_resp.json.return_value = {'error': 'bad'}
    mock_resp.status_code = 400

    # raise HTTPError with response attr
    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)

    with app.app_context():
        with pytest.raises(ClienteServiceError) as excinfo:
            crear_cliente_externo(minimal_cliente())

    assert excinfo.value.status_code == 400
    assert excinfo.value.message == mock_resp.json.return_value


@patch('src.services.clientes.requests.post')
def test_crear_cliente_connection_error(mock_post, app):
    mock_post.side_effect = requests.exceptions.RequestException('conn failed')

    with app.app_context():
        with pytest.raises(ClienteServiceError) as excinfo:
            crear_cliente_externo(minimal_cliente())

    assert excinfo.value.status_code == 503
    assert excinfo.value.message['codigo'] == 'ERROR_CONEXION'
