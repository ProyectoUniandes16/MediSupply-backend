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
            with patch('src.services.pedidos.requests.post', side_effect=requests.exceptions.RequestException('conn fail')):
                data = {'productos': [{'id': 1}], 'total': 10, 'cliente_id': 1}
                with pytest.raises(PedidoServiceError) as exc:
                    crear_pedido_externo(data, 'v@e.com')

    assert exc.value.status_code == 503


def test_crear_pedido_externo_success():
    # mock listar_vendedores_externo and requests.post happy path
    mock_vendor = {'items': [{'id': 'v-1'}]}
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {'id': 10, 'cliente_id': 1}

    with make_app_ctx():
        with patch('src.services.pedidos.listar_vendedores_externo', return_value=mock_vendor) as mock_lv:
            with patch('src.services.pedidos.requests.post', return_value=mock_response) as mock_post:
                data = {'productos': [{'id': 1}], 'total': 10, 'cliente_id': 1}
                result = crear_pedido_externo(data, 'v@e.com')

    assert result == {'id': 10, 'cliente_id': 1}
    mock_lv.assert_called_once()
    mock_post.assert_called_once()
