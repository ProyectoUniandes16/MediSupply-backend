import pytest

from src.services.pedidos import registrar_pedido, PedidoServiceError
from src.models.pedios import Pedido
from src.models.pedidos_productos import PedidoProducto


def test_registrar_pedido_none_raises():
    with pytest.raises(PedidoServiceError) as exc:
        registrar_pedido(None)

    assert exc.value.status_code == 400


def test_registrar_pedido_missing_fields():
    data = {'cliente_id': 1, 'total': 100}
    with pytest.raises(PedidoServiceError) as exc:
        registrar_pedido(data)

    assert exc.value.status_code == 400
    assert 'Campos faltantes' in exc.value.message.get('error', '')


def test_registrar_pedido_total_menor_cero():
    # use a negative total (truthy) so the "missing fields" check doesn't
    # intercept the flow; registrar_pedido then validates total <= 0.
    data = {'cliente_id': 1, 'total': -1, 'productos': [{'producto_id': 1, 'cantidad': 1, 'precio': 10}]}
    with pytest.raises(PedidoServiceError) as exc:
        registrar_pedido(data)

    assert exc.value.status_code == 400
    assert exc.value.message.get('codigo') == 'TOTAL_MENOR_CERO'


def test_registrar_pedido_productos_vacio():
    # Given the implementation checks `if not data.get(field)` when
    # detecting missing fields, an empty list for `productos` will be
    # considered missing. Assert that the service reports missing fields.
    data = {'cliente_id': 1, 'total': 100, 'productos': []}
    with pytest.raises(PedidoServiceError) as exc:
        registrar_pedido(data)

    assert exc.value.status_code == 400
    assert 'Campos faltantes' in exc.value.message.get('error', '')


def test_registrar_pedido_success(session):
    # happy path: persists pedido and pedido_producto
    data = {
        'cliente_id': 42,
        'total': 25.5,
        'productos': [
            {'producto_id': 7, 'cantidad': 2, 'precio': 12.75}
        ]
    }

    result = registrar_pedido(data)

    assert isinstance(result, dict)
    assert result['cliente_id'] == 42
    # Use approx to avoid float equality issues
    assert result['total'] == pytest.approx(25.5)
    assert 'id' in result

    # check DB state
    pedidos = session.query(Pedido).all()
    productos = session.query(PedidoProducto).all()

    assert len(pedidos) == 1
    assert len(productos) == 1


def test_registrar_pedido_save_exception(app, monkeypatch):
    # force Pedido.save to raise to exercise error handling
    def fake_save(self):
        # raise a more specific exception type to satisfy linters
        raise RuntimeError('db fail')

    monkeypatch.setattr(Pedido, 'save', fake_save)

    data = {
        'cliente_id': 1,
        'total': 10,
        'productos': [{'producto_id': 1, 'cantidad': 1, 'precio': 10}]
    }

    with pytest.raises(PedidoServiceError) as exc:
        registrar_pedido(data)

    assert exc.value.status_code == 500
    assert exc.value.message.get('codigo') == 'ERROR_GUARDAR_PEDIDO'
