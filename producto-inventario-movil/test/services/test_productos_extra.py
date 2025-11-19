import io
import pytest
import io
import pytest
from unittest.mock import patch
import requests

from src.services.productos import (
    _extract_productos,
    aplanar_productos_con_inventarios,
    consultar_productos_externo,
    obtener_producto_por_sku_externo,
    subir_video_producto_externo,
    ProductoServiceError,
)


def test_extract_productos_various_shapes():
    # list
    assert _extract_productos([{'id': 1}]) == [{'id': 1}]

    # payload with 'data'
    assert _extract_productos({'data': [{'id': 2}]}) == [{'id': 2}]
    # payload with 'productos'
    assert _extract_productos({'productos': [{'id': 3}]}) == [{'id': 3}]
    # payload with 'items'
    assert _extract_productos({'items': [{'id': 4}]}) == [{'id': 4}]
    # payload with 'results'
    assert _extract_productos({'results': [{'id': 5}]}) == [{'id': 5}]

    # unknown shapes
    assert _extract_productos({'foo': 'bar'}) == []


def test_aplanar_productos_con_inventarios_basic():
    data = {
        'data': [
            {'id': 1, 'totalInventario': 10, 'inventarios': [{'loc': 1}]},
            {'id': 2, 'totalInventario': 0},
            'not-a-mapping'
        ],
        'source': 'test'
    }
    out = aplanar_productos_con_inventarios(data)
    assert out['source'] == 'test'
    assert isinstance(out['data'], list)
    assert out['data'][0]['id'] == 1
    assert 'inventarios' not in out['data'][0]
    assert out['data'][0]['cantidad_disponible'] == 10


class DummyResp:
    def __init__(self, status_code=200, json_body=None, text=''):
        self.status_code = status_code
        self._json = json_body or {}
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if 400 <= self.status_code:
            raise requests.exceptions.HTTPError(response=self)


def test_consultar_productos_externo_non_200(monkeypatch):
    # simulate non-200 with JSON body
    def fake_get(url, params=None):
        return DummyResp(status_code=500, json_body={'error': 'boom'}, text='boom')

    monkeypatch.setattr('src.services.productos.requests.get', fake_get)

    from src import create_app
    app = create_app()
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            consultar_productos_externo({'q': 'x'})
    # When requests.raise_for_status() raises, the service wraps it as a
    # connection error with status 503.
    assert exc.value.status_code == 503


def test_consultar_productos_externo_request_exception(monkeypatch):
    def raise_req(*a, **kw):
        raise requests.exceptions.RequestException('conn')

    monkeypatch.setattr('src.services.productos.requests.get', raise_req)

    from src import create_app
    app = create_app()
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            consultar_productos_externo({'q': 'x'})
    assert exc.value.status_code == 503


def test_obtener_producto_por_sku_externo_empty_sku():
    with pytest.raises(ProductoServiceError) as exc:
        obtener_producto_por_sku_externo('')
    assert exc.value.status_code == 400


def test_obtener_producto_por_sku_externo_404(monkeypatch):
    def fake_get(url):
        return DummyResp(status_code=404, text='not found')

    monkeypatch.setattr('src.services.productos.requests.get', fake_get)

    from src import create_app
    app = create_app()
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            obtener_producto_por_sku_externo('NOSKU')
    assert exc.value.status_code == 404


def test_subir_video_producto_externo_statuses(monkeypatch):
    class DummyFileObj:
        def __init__(self, filename, stream, content_type='video/mp4'):
            self.filename = filename
            self.stream = stream
            self.content_type = content_type

    # Prepare a dummy file-like object expected by the uploader
    video_file = DummyFileObj('video.mp4', io.BytesIO(b'data'))

    # 404
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **k: DummyResp(status_code=404, text='nf'))
    from src import create_app
    app = create_app()
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            subir_video_producto_externo(1, video_file, 'desc', 'user')
    assert exc.value.status_code == 404

    # 400 with json
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **k: DummyResp(status_code=400, json_body={'error': 'bad'}, text='bad'))
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            subir_video_producto_externo(1, video_file, 'desc', 'user')
    assert exc.value.status_code == 400

    # 413
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **k: DummyResp(status_code=413, text='too big'))
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            subir_video_producto_externo(1, video_file, 'desc', 'user')
    assert exc.value.status_code == 413

    # non-201 other
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **k: DummyResp(status_code=500, text='err'))
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            subir_video_producto_externo(1, video_file, 'desc', 'user')
    assert exc.value.status_code == 500

    # timeout
    def raise_timeout(*a, **kw):
        raise requests.exceptions.Timeout('to')
    monkeypatch.setattr('src.services.productos.requests.post', raise_timeout)
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            subir_video_producto_externo(1, video_file, 'desc', 'user')
    assert exc.value.status_code == 504

    # request exception
    def raise_req(*a, **kw):
        raise requests.exceptions.RequestException('conn')
    monkeypatch.setattr('src.services.productos.requests.post', raise_req)
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            subir_video_producto_externo(1, video_file, 'desc', 'user')
    assert exc.value.status_code == 503
