import pytest
from werkzeug.datastructures import ImmutableMultiDict
from flask import Flask
from src.services.productos import ProductoServiceError

@pytest.fixture
def fake_config(monkeypatch):
    # Mockea la URL del microservicio
    monkeypatch.setattr('src.services.productos.config', type('C', (), {'PRODUCTO_URL': 'http://fake.url'}))

@pytest.fixture
def fake_requests_post(monkeypatch):
    # Fixture/fake para requests.post que retorna una instancia Response válida
    def _fake(status_code=201, resp_json=None, text="OK"):
        class Response:
            def __init__(self, status_code, resp_json, text):
                self.status_code = status_code
                self._json = resp_json or {"id": 1}
                self.text = text
            def json(self):
                return self._json
        return Response(status_code, resp_json, text)
    return _fake

def build_form_data(valid=True):
    datos = {
        'nombre': 'A',
        'codigo_sku': '111',
        'categoria': 'Bebida',
        'precio_unitario': '10.5',
        'condiciones_almacenamiento': 'Seco',
        'fecha_vencimiento': '2025-10-25',
        'proveedor_id': '42',
    }
    if not valid:
        datos.pop('nombre')
    return ImmutableMultiDict(datos)

def build_files(valid=True):
    if not valid:
        return {}
    class File:
        filename = 'file.pdf'
        stream = b'data'
        mimetype = 'application/pdf'
    return {'certificacion': File()}

def test_consultar_productos_externo_success(monkeypatch, fake_config):
    """La función debe retornar el JSON cuando el microservicio responde 200."""
    from src.services.productos import consultar_productos_externo

    class R:
        status_code = 200
        def json(self):
            return {'items': [{'id': 1}], 'total': 1}
        def raise_for_status(self):
            return None

    monkeypatch.setattr('src.services.productos.requests.get', lambda *a, **kw: R())

    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        res = consultar_productos_externo({'q': 'x'})
    assert isinstance(res, dict)
    assert res['total'] == 1


def test_consultar_productos_externo_backend_error(monkeypatch, fake_config):
    """Si el backend responde con status != 200 y body JSON, debe levantarse ProductoServiceError con ese body y status."""
    from src.services.productos import consultar_productos_externo

    class R:
        status_code = 400
        def json(self):
            return {'error': 'bad', 'codigo': 'ERR'}
        def raise_for_status(self):
            # Simular que raise_for_status no lanza excepción para permitir que la función maneje el status
            return None
        text = 'Bad Request'

    monkeypatch.setattr('src.services.productos.requests.get', lambda *a, **kw: R())

    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            consultar_productos_externo({'page': 1})

    assert exc.value.status_code == 400
    assert isinstance(exc.value.message, dict)
    assert exc.value.message['codigo'] == 'ERR'


def test_consultar_productos_externo_connection_error(monkeypatch, fake_config):
    """Si ocurre una excepción de requests (p. ej. RequestException), debe levantarse ProductoServiceError con codigo ERROR_CONEXION y status 503."""
    from src.services.productos import consultar_productos_externo
    import requests

    def raise_req(*a, **kw):
        raise requests.exceptions.RequestException('network')

    monkeypatch.setattr('src.services.productos.requests.get', raise_req)

    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        with pytest.raises(ProductoServiceError) as exc:
            consultar_productos_externo()

    assert exc.value.status_code == 503
    assert isinstance(exc.value.message, dict)
    assert exc.value.message.get('codigo') == 'ERROR_CONEXION'
