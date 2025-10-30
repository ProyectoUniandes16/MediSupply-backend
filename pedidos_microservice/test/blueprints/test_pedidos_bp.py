import pytest

from src.services.pedidos import PedidoServiceError
import src.blueprints.pedidos as pedidos_bp_module


def test_crear_pedido_success(client):
    data = {
        'cliente_id': 99,
        'total': 5.0,
        'productos': [{'producto_id': 1, 'cantidad': 1, 'precio': 5.0}]
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
