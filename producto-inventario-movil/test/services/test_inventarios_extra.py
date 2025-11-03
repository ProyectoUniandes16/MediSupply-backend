import pytest
from flask import Flask
from unittest.mock import MagicMock

from src.services.inventarios import (
    aplanar_productos_con_inventarios,
    _get_inventarios_by_producto,
    _get_from_microservice,
    actualizar_inventatrio_externo,
    _actualizar_inventario,
    InventarioServiceError,
)
from src.services.cache_client import CacheClient


def make_app():
    app = Flask(__name__)
    app.config.update({'INVENTARIOS_URL': 'http://inventarios:5009'})
    return app


def test_aplanar_productos_con_inventarios_removes_fields():
    data = {
        'data': [
            {
                'id': 1,
                'nombre': 'X',
                'inventarios': [{'id': 11}],
                'totalInventario': 7
            }
        ],
        'source': 'microservice'
    }

    res = aplanar_productos_con_inventarios(data)
    assert 'data' in res
    assert res['data'][0]['cantidad_disponible'] == 7
    assert 'inventarios' not in res['data'][0]
    assert res['source'] == 'microservice'


def test_get_inventarios_by_producto_cache_hit(monkeypatch):
    class FakeCache(CacheClient):
        def __init__(self):
            pass

        def get_inventarios_by_producto(self, producto_id: str):
            return [{'id': 'i1', 'cantidad': 4}, {'id': 'i2', 'cantidad': 1}]

    monkeypatch.setattr('src.services.inventarios.CacheClient.from_app_config', classmethod(lambda cls: FakeCache()))

    app = make_app()
    with app.app_context():
        res = _get_inventarios_by_producto('p-1')

    assert isinstance(res, dict)
    data = res.get('data')
    assert data and data['total'] == 2
    assert data['totalCantidad'] == 5


def test_get_from_microservice_success_and_error(monkeypatch):
    app = make_app()

    class R:
        status_code = 200

        def json(self):
            return {'inventarios': [{'id': 'x', 'cantidad': 2}]}

    monkeypatch.setattr('src.services.inventarios.requests.get', lambda *a, **kw: R())
    with app.app_context():
        lst = _get_from_microservice('p2')
    assert isinstance(lst, list)
    assert lst and lst[0]['id'] == 'x'

    # Simulate network error -> should return empty list (function handles exceptions)
    def raise_exc(*a, **kw):
        raise Exception('boom')

    monkeypatch.setattr('src.services.inventarios.requests.get', raise_exc)
    with app.app_context():
        lst2 = _get_from_microservice('p2')
    assert lst2 == []


def test_actualizar_inventatrio_externo_no_inventarios_raises(monkeypatch):
    # _get_inventarios_by_producto returns empty list
    monkeypatch.setattr('src.services.inventarios._get_inventarios_by_producto', lambda pid: {'data': {'inventarios': []}})
    app = make_app()
    with app.app_context():
        with pytest.raises(InventarioServiceError) as exc:
            actualizar_inventatrio_externo('p-x', -1)

    assert exc.value.status_code == 404


def test_actualizar_inventatrio_externo_calls_update_and_returns_true(monkeypatch):
    # Provide one inventario and patch _actualizar_inventario
    monkeypatch.setattr('src.services.inventarios._get_inventarios_by_producto', lambda pid: {'data': {'inventarios': [{'id': 'inv1', 'cantidad': 5}]}})
    monkeypatch.setattr('src.services.inventarios._actualizar_inventario', lambda inv_id, data: {'id': inv_id, **data})

    app = make_app()
    with app.app_context():
        ok = actualizar_inventatrio_externo('p-x', -2)
    assert ok is True


def test__actualizar_inventario_put_behavior(monkeypatch):
    app = make_app()

    class RespOK:
        status_code = 200

        def json(self):
            return {'id': 'inv1', 'cantidad': 9}

    class RespFail:
        status_code = 500
        content = b'error'

        def json(self):
            return {'error': 'fail'}

    monkeypatch.setattr('src.services.inventarios.current_app', app)
    monkeypatch.setattr('src.services.inventarios.requests.put', lambda *a, **kw: RespOK())
    res = _actualizar_inventario('inv1', {'cantidad': 9})
    assert res['cantidad'] == 9

    monkeypatch.setattr('src.services.inventarios.requests.put', lambda *a, **kw: RespFail())
    with pytest.raises(Exception):
        _actualizar_inventario('inv1', {'cantidad': 9})
