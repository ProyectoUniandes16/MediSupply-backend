import pytest
import requests
from unittest.mock import patch, MagicMock

from src.services.pedidos import crear_pedido_externo, PedidoServiceError


def make_app_ctx():
    from src import create_app
    app = create_app()
    return app.app_context()


def test_crear_pedido_externo_no_datos():
    with make_app_ctx():
        with pytest.raises(PedidoServiceError) as exc:
            crear_pedido_externo(None, 'v@e.com')

    assert exc.value.status_code == 400
    assert exc.value.message.get('codigo') == 'DATOS_VACIOS'


def test_crear_pedido_externo_missing_fields():
    with make_app_ctx():
        data = {'total': 10}
        with pytest.raises(PedidoServiceError) as exc:
            crear_pedido_externo(data, 'v@e.com')

    assert exc.value.status_code == 400
    assert 'Campos faltantes' in exc.value.message.get('error', '')


def test_crear_pedido_externo_productos_invalid():
    with make_app_ctx():
        data = {'productos': 'not-a-list', 'total': 10, 'cliente_id': 1}
        with pytest.raises(PedidoServiceError) as exc:
            crear_pedido_externo(data, 'v@e.com')

    assert exc.value.status_code == 400
    assert exc.value.message.get('codigo') == 'PRODUCTOS_INVALIDOS'


def test_crear_pedido_externo_vendedor_not_found():
    # mock listar_vendedores_externo to return no items
    with make_app_ctx():
        with patch('src.services.pedidos.listar_vendedores_externo', return_value={'items': []}):
            data = {'productos': [{'id': 1}], 'total': 10, 'cliente_id': 1}
            with pytest.raises(PedidoServiceError) as exc:
                crear_pedido_externo(data, 'v@e.com')

    assert exc.value.status_code == 404
    assert exc.value.message.get('codigo') == 'VENDEDOR_NO_ENCONTRADO'


def test_crear_pedido_externo_requests_error():
    # mock listar_vendedores_externo to return a vendor, but requests.post to raise
    mock_vendor = {'items': [{'id': 'v-1'}]}
    with make_app_ctx():
        with patch('src.services.pedidos.listar_vendedores_externo', return_value=mock_vendor):
            # evitar consulta real a productos (se parchea para que retorne lista vacía)
            with patch('src.services.pedidos.get_productos_con_inventarios', return_value={'data': []}):
                # evitar que la actualización de inventario intente llamadas externas
                with patch('src.services.pedidos.actualizar_inventatrio_externo', return_value=True):
                    with patch('src.services.pedidos.requests.post', side_effect=requests.exceptions.RequestException('conn fail')):
                        data = {'productos': [{'id': 1}], 'total': 10, 'cliente_id': 1}
                        with pytest.raises(PedidoServiceError) as exc:
                            crear_pedido_externo(data, 'v@e.com')

    assert exc.value.status_code == 503
