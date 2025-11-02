import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from unittest.mock import patch

from src import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def token(app):
    with app.app_context():
        return create_access_token(identity='tester')


def test_listar_productos_aggregated_ok(client, token, monkeypatch):
    expected = {
        'data': [
            {'id': 1, 'nombre': 'A', 'inventarios': [], 'totalInventario': 0, 'inventariosSource': 'cache'}
        ],
        'total': 1,
        'source': 'cache'
    }

    monkeypatch.setattr('src.blueprints.producto.get_productos_con_inventarios', lambda params=None: expected)

    resp = client.get('/producto', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == expected


def test_listar_productos_aggregated_propagates_domain_errors(client, token, monkeypatch):
    from src.services.inventarios import InventarioServiceError
    err = InventarioServiceError({'error': 'fallo', 'codigo': 'ERROR_CONEXION'}, 503)

    monkeypatch.setattr('src.blueprints.producto.get_productos_con_inventarios', lambda params=None: (_ for _ in ()).throw(err))

    resp = client.get('/producto', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 503
    assert resp.get_json()['codigo'] == 'ERROR_CONEXION'


def test_listar_productos_requires_auth(client):
    resp = client.get('/producto')
    assert resp.status_code == 401
