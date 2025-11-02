import pytest
from unittest.mock import patch
from src import create_app
from flask_jwt_extended import create_access_token
from src.services.pedidos import PedidoServiceError


def test_crear_pedido_blueprint_success():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    data = {'productos': [{'id': 1}], 'total': 10, 'cliente_id': 1}

    with patch('src.blueprints.pedidos.decode_jwt', return_value={'user': {'email': 'v@e.com'}}):
        with patch('src.blueprints.pedidos.crear_pedido_externo', return_value={'id': 123}) as mock_cp:
            resp = client.post('/pedido', json=data, headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 201
    assert resp.get_json() == {'id': 123}
    mock_cp.assert_called_once()


def test_crear_pedido_blueprint_service_error():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    with patch('src.blueprints.pedidos.decode_jwt', return_value={'user': {'email': 'v@e.com'}}):
        with patch('src.blueprints.pedidos.crear_pedido_externo', side_effect=PedidoServiceError({'error': 'X'}, 400)):
            resp = client.post('/pedido', json={}, headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 400
    assert resp.get_json().get('error') == 'X'


def test_crear_pedido_blueprint_unexpected_error():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    with patch('src.blueprints.pedidos.decode_jwt', return_value={'user': {'email': 'v@e.com'}}):
        with patch('src.blueprints.pedidos.crear_pedido_externo', side_effect=Exception('boom')):
            resp = client.post('/pedido', json={}, headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 500
    assert 'Error interno del servidor' in resp.get_json().get('error', '')
