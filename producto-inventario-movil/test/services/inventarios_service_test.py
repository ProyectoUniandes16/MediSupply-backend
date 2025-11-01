import pytest
from flask import Flask
from unittest.mock import patch, Mock
from typing import Any, Dict

from src.services.inventarios import (
    _extract_productos,
    _resolve_inventarios_from_cache,
    _fetch_inventarios_from_upstream,
    _upsert_cache,
    get_productos_con_inventarios,
    InventarioServiceError,
)
from src.services.cache_client import CacheClient


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update({
        'INVENTARIOS_URL': 'http://inventarios:5009',
        'REDIS_SERVICE_URL': 'http://redis_service:5011',
        'CACHE_DEFAULT_TTL': 60
    })
    return app


# ---- Unit tests for helpers ----

def test_extract_productos_variants():
    assert _extract_productos([{'id':1}]) == [{'id':1}]
    assert _extract_productos({'productos':[{'id':2}]}) == [{'id':2}]
    assert _extract_productos({'data':[{'id':3}]}) == [{'id':3}]
    assert _extract_productos({'items':[{'id':4}]}) == [{'id':4}]
    assert _extract_productos({'results':[{'id':5}]}) == [{'id':5}]
    assert _extract_productos({'otro': 1}) == []
    assert _extract_productos('not a list') == []


def test_resolve_inventarios_from_cache_list_payload():
    class FakeCache(CacheClient):
        def __init__(self): pass
        def get_inventarios_by_producto(self, producto_id: str):
            return [{'cantidad': 2}, {'cantidad': 3}]
    payload = _resolve_inventarios_from_cache(FakeCache(), '10')
    assert payload['totalInventario'] == 5
    assert payload['source'] == 'cache'


def test_resolve_inventarios_from_cache_dict_payload():
    class FakeCache(CacheClient):
        def __init__(self): pass
        def get_inventarios_by_producto(self, producto_id: str):
            return {'inventarios': [{'cantidad': 7}], 'totalInventario': 7}
    payload = _resolve_inventarios_from_cache(FakeCache(), '10')
    assert payload['totalInventario'] == 7
    assert payload['inventarios'] == [{'cantidad':7}]


def test_resolve_inventarios_from_cache_malformed():
    class FakeCache(CacheClient):
        def __init__(self): pass
        def get_inventarios_by_producto(self, producto_id: str):
            return 'oops'
    payload = _resolve_inventarios_from_cache(FakeCache(), '10')
    assert payload is None


# ---- Upstream fetch tests ----

def test_fetch_inventarios_from_upstream_success(app, monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {'inventarios': [{'cantidad': 2}, {'cantidad': 8}]}
    monkeypatch.setattr('src.services.inventarios.requests.get', lambda *a, **kw: R())

    with app.app_context():
        payload = _fetch_inventarios_from_upstream('42')

    assert payload['totalInventario'] == 10
    assert payload['source'] == 'microservice'


def test_fetch_inventarios_from_upstream_error_status(app, monkeypatch):
    class R:
        status_code = 500
        text = 'boom'
        def json(self):
            return {'error': 'boom', 'codigo': 'ERR'}
    monkeypatch.setattr('src.services.inventarios.requests.get', lambda *a, **kw: R())

    with app.app_context():
        with pytest.raises(InventarioServiceError) as exc:
            _fetch_inventarios_from_upstream('42')

    assert exc.value.status_code == 500


def test_fetch_inventarios_from_upstream_connection_error(app, monkeypatch):
    import requests
    def raise_conn(*a, **kw):
        raise requests.RequestException('net')
    monkeypatch.setattr('src.services.inventarios.requests.get', raise_conn)

    with app.app_context():
        with pytest.raises(InventarioServiceError) as exc:
            _fetch_inventarios_from_upstream('42')
    assert exc.value.status_code == 503


# ---- Integration of get_productos_con_inventarios (with mocks) ----

def test_get_productos_con_inventarios_cache_hit(app, monkeypatch):
    # Productos externo devolverá dos productos
    productos_payload = {'productos': [
        {'id': 1, 'nombre': 'A'},
        {'id': 2, 'nombre': 'B'}
    ]}

    monkeypatch.setattr('src.services.inventarios.consultar_productos_externo', lambda params=None: productos_payload)

    class FakeCache(CacheClient):
        def __init__(self): pass
        def get_inventarios_by_producto(self, producto_id: str):
            return {'inventarios': [{'cantidad': 5}], 'totalInventario': 5}
        def set_inventarios_by_producto(self, *a, **k):
            pytest.fail('No debería escribir en cache en cache-hit')

    monkeypatch.setattr('src.services.inventarios.CacheClient.from_app_config', classmethod(lambda cls: FakeCache()))

    with app.app_context():
        res = get_productos_con_inventarios()

    assert res['total'] == 2
    assert res['source'] == 'cache'
    assert all('totalInventario' in p for p in res['data'])
    assert all(p['inventariosSource'] == 'cache' for p in res['data'])


def test_get_productos_con_inventarios_cache_miss_fetch_and_store(app, monkeypatch):
    productos_payload = {'productos': [ {'id': 1} ]}
    monkeypatch.setattr('src.services.inventarios.consultar_productos_externo', lambda params=None: productos_payload)

    class FakeCache(CacheClient):
        def __init__(self): self.set_calls = []
        def get_inventarios_by_producto(self, producto_id: str):
            return None
        def set_inventarios_by_producto(self, producto_id: str, value: Dict[str, Any], ttl=None):
            self.set_calls.append((producto_id, value))
            return True
    fake_cache = FakeCache()

    monkeypatch.setattr('src.services.inventarios.CacheClient.from_app_config', classmethod(lambda cls: fake_cache))

    class R:
        status_code = 200
        def json(self):
            return {'inventarios': [{'cantidad': 3}]}
    monkeypatch.setattr('src.services.inventarios.requests.get', lambda *a, **kw: R())

    with app.app_context():
        res = get_productos_con_inventarios()

    assert res['total'] == 1
    assert res['source'] == 'microservices'
    assert fake_cache.set_calls, 'Debe escribir en cache tras cache-miss'
    producto = res['data'][0]
    assert producto['totalInventario'] == 3


def test_get_productos_con_inventarios_skips_invalid_products(app, monkeypatch):
    productos_payload = {'productos': [ {'id': 1}, 'x', {} ]}
    monkeypatch.setattr('src.services.inventarios.consultar_productos_externo', lambda params=None: productos_payload)

    class FakeCache(CacheClient):
        def __init__(self): pass
        def get_inventarios_by_producto(self, producto_id: str):
            return {'inventarios': [], 'totalInventario': 0}
    monkeypatch.setattr('src.services.inventarios.CacheClient.from_app_config', classmethod(lambda cls: FakeCache()))

    with app.app_context():
        res = get_productos_con_inventarios()

    assert res['total'] == 1
    assert len(res['data']) == 1
