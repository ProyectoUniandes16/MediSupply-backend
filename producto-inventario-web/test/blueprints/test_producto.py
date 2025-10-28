import io
import pytest
from flask_jwt_extended import create_access_token

from src import create_app
from src.services.productos import ProductoServiceError


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity='user-1')
    return {'Authorization': f'Bearer {token}'}


def test_producto_create_and_query_paths(client, mocker, auth_headers):
    mock_create = mocker.patch(
        'src.blueprints.producto.crear_producto_externo',
        side_effect=[{'id': 10}, ProductoServiceError({'error': 'duplicado'}, 409), Exception('boom')]
    )
    mocker.patch('src.blueprints.producto.get_jwt_identity', return_value='user-1')

    response = client.post('/producto', headers=auth_headers, data={'nombre': 'Prod'})
    assert response.status_code == 201
    assert response.get_json()['data']['id'] == 10

    response = client.post('/producto', headers=auth_headers, data={'nombre': 'Prod'})
    assert response.status_code == 409
    assert response.get_json() == {'error': 'duplicado'}

    response = client.post('/producto', headers=auth_headers, data={'nombre': 'Prod'})
    assert response.status_code == 500
    assert response.get_json()['codigo'] == 'ERROR_INESPERADO'
    mock_create.assert_called()

    mock_consulta = mocker.patch(
        'src.blueprints.producto.consultar_productos_externo',
        side_effect=[{'items': [{'id': 1}]}, ProductoServiceError({'error': 'fuera'}, 503), Exception('fallo')]
    )

    response = client.get('/producto', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['data']['items'] == [{'id': 1}]

    response = client.get('/producto', headers=auth_headers)
    assert response.status_code == 503

    response = client.get('/producto', headers=auth_headers)
    assert response.status_code == 500
    assert response.get_json()['codigo'] == 'ERROR_INESPERADO'
    mock_consulta.assert_called()

    mock_detalle = mocker.patch(
        'src.blueprints.producto.obtener_detalle_producto_externo',
        side_effect=[{'id': 7}, ProductoServiceError({'error': 'no'}, 404), Exception('err')]
    )

    response = client.get('/producto/7', headers=auth_headers)
    assert response.status_code == 200

    response = client.get('/producto/7', headers=auth_headers)
    assert response.status_code == 404

    response = client.get('/producto/7', headers=auth_headers)
    assert response.status_code == 500
    mock_detalle.assert_called()

    mock_sku = mocker.patch(
        'src.blueprints.producto.obtener_producto_por_sku_externo',
        side_effect=[{'id': 5}, ProductoServiceError({'error': 'no'}, 404)]
    )

    response = client.get('/producto/sku/ABC', headers=auth_headers)
    assert response.status_code == 200

    response = client.get('/producto/sku/ABC', headers=auth_headers)
    assert response.status_code == 404
    mock_sku.assert_called()


def test_producto_batch_variants(client, mocker, auth_headers):
    mocker.patch('src.blueprints.producto.get_jwt_identity', return_value='user-1')
    response = client.post('/producto-batch', headers=auth_headers)
    assert response.status_code == 400

    mock_batch = mocker.patch('src.blueprints.producto.procesar_y_enviar_producto_batch')

    def make_data():
        return {'file': (io.BytesIO(b'csv'), 'test.csv')}

    mock_batch.return_value = {'ok': True, 'status': 200, 'payload': {'total': 1}}
    response = client.post('/producto-batch', headers=auth_headers, data=make_data(), content_type='multipart/form-data')
    assert response.status_code == 200

    mock_batch.return_value = {'ok': False, 'status': 422, 'payload': {'error': 'bad', 'codigo': 'ERR'}}
    response = client.post('/producto-batch', headers=auth_headers, data=make_data(), content_type='multipart/form-data')
    assert response.status_code == 422

    mock_batch.return_value = {'ok': False, 'status': 400, 'payload': 'mensaje'}
    response = client.post('/producto-batch', headers=auth_headers, data=make_data(), content_type='multipart/form-data')
    assert response.status_code == 400

    mock_batch.side_effect = ProductoServiceError({'error': 'servicio'}, 503)
    response = client.post('/producto-batch', headers=auth_headers, data=make_data(), content_type='multipart/form-data')
    assert response.status_code == 503


def test_producto_download_paths(client, mocker, auth_headers):
    mock_download = mocker.patch(
        'src.blueprints.producto.descargar_certificacion_producto_externo',
        side_effect=[(b'%PDF', 'cert.pdf', 'application/pdf'), ProductoServiceError({'error': 'no'}, 404), Exception('boom')]
    )

    response = client.get('/producto/3/certificacion', headers=auth_headers)
    assert response.status_code == 200
    assert response.data == b'%PDF'

    response = client.get('/producto/3/certificacion', headers=auth_headers)
    assert response.status_code == 404

    response = client.get('/producto/3/certificacion', headers=auth_headers)
    assert response.status_code == 500
    assert response.get_json()['codigo'] == 'ERROR_INESPERADO'
    mock_download.assert_called()
