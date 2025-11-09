import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

from src.blueprints import clientes as clientes_module


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


def make_token():
    return {'user': {'email': 'v@e.com'}}


@patch('src.blueprints.clientes.decode_jwt')
@patch('src.blueprints.clientes.crear_cliente_externo')
def test_crear_cliente_blueprint_success(mock_service, mock_decode, app):
    mock_service.return_value = {'id': 'c1'}
    mock_decode.return_value = make_token()

    with app.test_request_context('/cliente', method='POST', json=minimal_cliente(), headers={'Authorization': 'Bearer tok'}):
        # Llamar a la función sin pasar por el decorador jwt_required
        resp, status = clientes_module.crear_cliente.__wrapped__()

    assert status == 201
    assert resp.get_json() == {'id': 'c1'}
    mock_service.assert_called_once()


@patch('src.blueprints.clientes.decode_jwt')
@patch('src.blueprints.clientes.crear_cliente_externo')
def test_crear_cliente_blueprint_service_error(mock_service, mock_decode, app):
    from src.services.clientes import ClienteServiceError

    mock_service.side_effect = ClienteServiceError({'error': 'bad'}, 400)
    mock_decode.return_value = make_token()

    with app.test_request_context('/cliente', method='POST', json=minimal_cliente(), headers={'Authorization': 'Bearer tok'}):
        resp, status = clientes_module.crear_cliente.__wrapped__()

    assert status == 400
    assert resp.get_json() == {'error': 'bad'}


@patch('src.blueprints.clientes.decode_jwt')
@patch('src.blueprints.clientes.crear_cliente_externo')
def test_crear_cliente_blueprint_unexpected_exception(mock_service, mock_decode, app):
    mock_service.side_effect = Exception('boom')
    mock_decode.return_value = make_token()

    with app.test_request_context('/cliente', method='POST', json=minimal_cliente(), headers={'Authorization': 'Bearer tok'}):
        resp, status = clientes_module.crear_cliente.__wrapped__()

    assert status == 500
    body = resp.get_json()
    assert 'Error interno del servidor' in body['error']


@patch('src.blueprints.clientes.decode_jwt')
@patch('src.blueprints.clientes.listar_clientes_vendedor_externo')
def test_listar_clientes_blueprint_success(mock_service, mock_decode, app):
    mock_service.return_value = {'data': [{'id': 1}]}
    mock_decode.return_value = make_token()

    with app.test_request_context('/cliente', method='GET', headers={'Authorization': 'Bearer tok'}):
        resp, status = clientes_module.listar_clientes.__wrapped__()

    assert status == 200
    assert resp.get_json() == {'data': [{'id': 1}]}


@patch('src.blueprints.clientes.decode_jwt')
@patch('src.blueprints.clientes.listar_clientes_vendedor_externo')
def test_listar_clientes_blueprint_service_error(mock_service, mock_decode, app):
    from src.services.clientes import ClienteServiceError

    mock_service.side_effect = ClienteServiceError({'error': 'x'}, 418)
    mock_decode.return_value = make_token()

    with app.test_request_context('/cliente', method='GET', headers={'Authorization': 'Bearer tok'}):
        resp, status = clientes_module.listar_clientes.__wrapped__()

    assert status == 418
    assert resp.get_json() == {'error': 'x'}
