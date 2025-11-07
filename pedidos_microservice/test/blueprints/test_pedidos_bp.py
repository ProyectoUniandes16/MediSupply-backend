import pytest

from src.services.pedidos import PedidoServiceError
import src.blueprints.pedidos as pedidos_bp_module


def test_crear_pedido_success(client):
    data = {
        'cliente_id': 99,
        'total': 5.0,
        'productos': [{'id': 1, 'cantidad': 1, 'precio': 5.0}]
    }

    response = client.post('/pedido', json=data)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['cliente_id'] == 99


def test_crear_pedido_service_error(client, monkeypatch):
    # monkeypatch the registrar_pedido used by the blueprint to raise a service error
    def raise_service_error(data):
        raise PedidoServiceError({'error': 'bad'}, 400)

    monkeypatch.setattr(pedidos_bp_module, 'registrar_pedido', raise_service_error)

    response = client.post('/pedido', json={'cliente_id': 1})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'bad'}


def test_crear_pedido_unexpected_exception(client, monkeypatch):
    # monkeypatch to raise a generic exception and expect 500
    def raise_exc(data):
        # use a specific exception type for clarity
        raise RuntimeError('boom')

    monkeypatch.setattr(pedidos_bp_module, 'registrar_pedido', raise_exc)

    response = client.post('/pedido', json={'cliente_id': 1})
    assert response.status_code == 500
    body = response.get_json()
    assert body.get('codigo') == 'ERROR_INTERNO_SERVIDOR'


def test_obtener_pedidos_without_filters(client, session):
    # seed pedidos directly in DB
    from src.models.pedios import Pedido

    p1 = Pedido(cliente_id=11, estado='pendiente', total=1.0, vendedor_id='vA')
    p2 = Pedido(cliente_id=12, estado='pendiente', total=2.0, vendedor_id='vB')
    session.add(p1)
    session.add(p2)
    session.commit()

    response = client.get('/pedido')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data['data'], list)
    assert len(data['data']) >= 2


def test_obtener_pedidos_filtering(client, session):
    from src.models.pedios import Pedido

    p = Pedido(cliente_id=55, estado='pendiente', total=3.0, vendedor_id='X123')
    session.add(p)
    session.commit()

    # filter by vendedor
    response = client.get('/pedido?vendedor_id=X123')
    assert response.status_code == 200
    data = response.get_json()['data']
    assert all(item.get('vendedor_id') == 'X123' for item in data)

    # filter by cliente
    response = client.get('/pedido?cliente_id=55')
    assert response.status_code == 200
    data = response.get_json()['data']
    assert all(item.get('cliente_id') == 55 for item in data)
