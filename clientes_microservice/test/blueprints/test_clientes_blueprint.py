import json
import pytest
from src.services.cliente_service import ClienteServiceError
from src.blueprints.clientes import clientes_bp

def test_crear_cliente_exito(client, mocker):
    payload = {
        'nombre': 'Empresa S.A.',
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'luis@empresa.com',
        'correo_empresa': 'contacto@empresa.com',
        'telefono_contacto': '5512345678',
        'nit': 'A12345678',
        'direccion': 'Calle Falsa 123'
    }
    mock_response = {'data': {'cliente': {'id': 1, 'nombre': payload['nombre']}, 'message': 'Cliente creado exitosamente'}}
    mocker.patch('src.blueprints.clientes.register_cliente', return_value=mock_response)

    resp = client.post('/cliente', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'data' in data
    assert data['data']['cliente']['nombre'] == payload['nombre']


def test_crear_cliente_service_error(client, mocker):
    payload = {'nombre': 'X'}
    err = ClienteServiceError({'error': 'Campos faltantes'}, 400)
    mocker.patch('src.blueprints.clientes.register_cliente', side_effect=err)

    resp = client.post('/cliente', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'Campos faltantes'


def test_crear_cliente_unexpected_error(client, mocker):
    payload = {'nombre': 'X'}
    mocker.patch('src.blueprints.clientes.register_cliente', side_effect=Exception('boom'))

    resp = client.post('/cliente', json=payload)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data['codigo'] == 'ERROR_INTERNO_SERVIDOR'
