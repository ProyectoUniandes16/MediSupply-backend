import io
from unittest.mock import patch
from flask_jwt_extended import create_access_token
from src import create_app


def test_consultar_productos_blueprint_success():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    fake_data = {'data': [{'id': 1, 'totalInventario': 2, 'inventarios': []}], 'source': 'test'}

    with patch('src.blueprints.producto.get_productos_con_inventarios', return_value=fake_data):
        with patch('src.blueprints.producto.aplanar_productos_con_inventarios', return_value={'data': [{'id': 1}], 'source': 'test'}):
            resp = client.get('/producto', headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 200
    assert resp.get_json()['data'][0]['id'] == 1


def test_subir_video_producto_missing_file():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    resp = client.post('/producto/1/videos', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 400
    assert resp.get_json()['codigo'] == 'ARCHIVO_FALTANTE'


def test_subir_video_producto_missing_description():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    # send file but no descripcion
    data = {
        'video': (io.BytesIO(b'data'), 'video.mp4')
    }
    resp = client.post('/producto/1/videos', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 400
    assert resp.get_json()['codigo'] == 'DESCRIPCION_FALTANTE'


def test_subir_video_producto_success(monkeypatch):
    app = create_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity='tester')

    # patch subir_video_producto_externo to return success
    monkeypatch.setattr('src.blueprints.producto.subir_video_producto_externo', lambda **kw: {'id': 123})
    monkeypatch.setattr('src.blueprints.producto.get_jwt_identity', lambda: 'tester')

    data = {
        'video': (io.BytesIO(b'data'), 'video.mp4'),
        'descripcion': 'prueba'
    }

    resp = client.post('/producto/1/videos', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201
    assert resp.get_json()['id'] == 123
