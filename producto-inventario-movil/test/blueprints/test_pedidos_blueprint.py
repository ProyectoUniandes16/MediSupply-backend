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


def test_listar_pedidos_blueprint_success():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    datos_esperados = {'data': [{'id': 1}]}

    with patch('src.blueprints.pedidos.decode_jwt', return_value={'user': {'email': 'v@e.com'}}):
        with patch('src.blueprints.pedidos.listar_pedidos_externo', return_value=datos_esperados) as mock_listar:
            resp = client.get('/pedido', headers={'Authorization': f'Bearer {token}'}, query_string={'cliente_id': '5'})

    assert resp.status_code == 200
    assert resp.get_json() == datos_esperados
    mock_listar.assert_called_once_with(filtros={'cliente_id': '5'}, email='v@e.com', rol=None)


def test_listar_pedidos_blueprint_service_error():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    with patch('src.blueprints.pedidos.decode_jwt', return_value={'user': {'email': 'v@e.com'}}):
        with patch(
            'src.blueprints.pedidos.listar_pedidos_externo',
            side_effect=PedidoServiceError({'error': 'X'}, 400)
        ):
            resp = client.get('/pedido', headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 400
    assert resp.get_json().get('error') == 'X'


def test_listar_pedidos_blueprint_unexpected_error():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    with patch('src.blueprints.pedidos.decode_jwt', return_value={'user': {'email': 'v@e.com'}}):
        with patch('src.blueprints.pedidos.listar_pedidos_externo', side_effect=Exception('boom')):
            resp = client.get('/pedido', headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 500
    assert 'Error interno del servidor' in resp.get_json().get('error', '')


def test_detalle_pedido_blueprint_success():
    app = create_app()
    client = app.test_client()

    detalle = {
        'data': {
            'id': 1,
            'productos': [
                {'producto_id': 10, 'cantidad': 2}
            ],
            'cliente_id': 1
        }
    }

    with patch('src.blueprints.pedidos.detalle_pedido_externo', return_value=detalle):
        with patch('src.blueprints.pedidos.obtener_detalle_producto_externo', return_value={'producto': {'id': 10, 'nombre': 'Producto X'}}):
            with patch('src.blueprints.pedidos.obtener_detalle_cliente_externo', return_value={'data': {'id': 1, 'nombre': 'Cliente X'}}):
                resp = client.get('/pedido/1')

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['data']['productos'][0]['cantidad'] == 2
    assert data['data']['productos'][0]['producto']['id'] == 10
    # cliente debe estar incluido en el resultado y contener los datos mockeados
    assert data['data']['cliente']['id'] == 1
    assert data['data']['cliente']['nombre'] == 'Cliente X'


def test_detalle_pedido_blueprint_unexpected_error():
    app = create_app()
    client = app.test_client()

    with patch('src.blueprints.pedidos.detalle_pedido_externo', side_effect=Exception('boom')):
        resp = client.get('/pedido/123')

    assert resp.status_code == 500
    assert resp.get_json().get('error') == 'Error interno del servidor'
