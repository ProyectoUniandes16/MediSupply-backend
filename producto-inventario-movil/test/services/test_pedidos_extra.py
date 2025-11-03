import pytest
import requests
from unittest.mock import patch, MagicMock

from src.services.pedidos import crear_pedido_externo, PedidoServiceError


def test_crear_pedido_externo_success(monkeypatch):
    mock_vendor = {'items': [{'id': 'v-1'}]}

    monkeypatch.setattr('src.services.pedidos.listar_vendedores_externo', lambda filters=None: mock_vendor)
    monkeypatch.setattr('src.services.pedidos.validate_order_against_products', lambda items, prod: {'valid': True, 'errors': []})
    monkeypatch.setattr('src.services.pedidos.actualizar_inventatrio_externo', lambda pid, adj: True)

    class Resp:
        status_code = 201

        def json(self):
            return {'id': 'pedido-1', 'status': 'created'}

    monkeypatch.setattr('src.services.pedidos.requests.post', lambda *a, **kw: Resp())

    data = {'productos': [{'id': 1, 'cantidad': 1}], 'total': 100, 'cliente_id': 1}
    # call inside a Flask app context because code logs to current_app
    from src import create_app
    app = create_app()
    with app.app_context():
        # evitar que la función real consulte productos (externo)
        monkeypatch.setattr('src.services.pedidos.get_productos_con_inventarios', lambda params=None: {'data': []})
        res = crear_pedido_externo(data, 'v@e.com')

    assert res['id'] == 'pedido-1'


def test_crear_pedido_externo_inventory_update_failure_propagates(monkeypatch):
    mock_vendor = {'items': [{'id': 'v-1'}]}
    monkeypatch.setattr('src.services.pedidos.listar_vendedores_externo', lambda filters=None: mock_vendor)
    monkeypatch.setattr('src.services.pedidos.validate_order_against_products', lambda items, prod: {'valid': True, 'errors': []})

    # Simulate inventory update failing by raising an exception
    def fail_update(pid, adj):
        raise Exception('inventory update failed')

    monkeypatch.setattr('src.services.pedidos.actualizar_inventatrio_externo', fail_update)

    data = {'productos': [{'id': 1, 'cantidad': 1}], 'total': 100, 'cliente_id': 1}
    from src import create_app
    app = create_app()
    with app.app_context():
        with pytest.raises(Exception):
            crear_pedido_externo(data, 'v@e.com')
