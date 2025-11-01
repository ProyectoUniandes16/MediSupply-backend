import pytest

from src import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_inventarios_read_endpoints(client, mocker):
    mocker.patch(
        'src.blueprints.inventarios.InventariosService.get_inventarios_by_producto',
        return_value={'productoId': '123', 'inventarios': [{'cantidad': 3}], 'total': 1, 'totalCantidad': 3, 'source': 'cache'}
    )
    mocker.patch('src.blueprints.inventarios.InventariosService.get_total_disponible', return_value=5)

    response = client.get('/productos/123/inventarios')
    assert response.status_code == 200
    assert response.get_json()['totalCantidad'] == 3

    response = client.get('/productos/123/disponible')
    assert response.status_code == 200
    assert response.get_json()['totalDisponible'] == 5

    cache_instance = mocker.Mock()
    cache_instance.is_available.return_value = True
    cache_factory = mocker.patch('src.services.cache_client.CacheClient', return_value=cache_instance)

    response = client.get('/health/cache')
    assert response.status_code == 200
    assert response.get_json()['cache'] == 'available'

    cache_instance.is_available.return_value = False
    response = client.get('/health/cache')
    assert response.status_code == 503
    assert response.get_json()['cache'] == 'unavailable'

    cache_factory.side_effect = Exception('boom')
    response = client.get('/health/cache')
    assert response.status_code == 500
    assert response.get_json()['cache'] == 'error'


def test_inventarios_input_validation(client):
    response = client.post('/inventarios', data='{}', content_type='application/json')
    assert response.status_code == 400

    response = client.put('/inventarios/abc', data='{}', content_type='application/json')
    assert response.status_code == 400

    response = client.post('/inventarios/abc/ajustar', json={'usuario': 'tester'})
    assert response.status_code == 400

    response = client.post('/inventarios/abc/ajustar', json={'ajuste': 'no-int', 'usuario': 'tester'})
    assert response.status_code == 400


def test_inventarios_write_operations(client, mocker):
    crear_mock = mocker.patch(
        'src.blueprints.inventarios.InventariosService.crear_inventario',
        side_effect=[{'id': 'inv-1'}, Exception('ya existe inventario')]
    )

    response = client.post('/inventarios', json={'productoId': '1', 'cantidad': 5})
    assert response.status_code == 201
    assert response.get_json()['id'] == 'inv-1'

    response = client.post('/inventarios', json={'productoId': '1', 'cantidad': 5})
    assert response.status_code == 400
    assert 'Error' in response.get_json()['error']
    crear_mock.assert_called()

    actualizar_mock = mocker.patch(
        'src.blueprints.inventarios.InventariosService.actualizar_inventario',
        side_effect=[{'id': 'inv-1', 'cantidad': 7}, Exception('no encontrado'), Exception('ya existe'), Exception('otra cosa')]
    )

    response = client.put('/inventarios/inv-1', json={'cantidad': 7})
    assert response.status_code == 200
    assert response.get_json()['cantidad'] == 7

    response = client.put('/inventarios/inv-1', json={'cantidad': 7})
    assert response.status_code == 404

    response = client.put('/inventarios/inv-1', json={'cantidad': 7})
    assert response.status_code == 400

    response = client.put('/inventarios/inv-1', json={'cantidad': 7})
    assert response.status_code == 500
    actualizar_mock.assert_called()

    eliminar_mock = mocker.patch(
        'src.blueprints.inventarios.InventariosService.eliminar_inventario',
        side_effect=[True, Exception('no encontrado'), Exception('error grave')]
    )

    response = client.delete('/inventarios/inv-1', json={'usuario': 'tester'})
    assert response.status_code == 200

    response = client.delete('/inventarios/inv-1', json={'usuario': 'tester'})
    assert response.status_code == 404

    response = client.delete('/inventarios/inv-1', json={'usuario': 'tester'})
    assert response.status_code == 500
    eliminar_mock.assert_called()

    ajustar_mock = mocker.patch(
        'src.blueprints.inventarios.InventariosService.ajustar_cantidad',
        side_effect=[{'cantidad': 10}, Exception('no encontrado'), Exception('negativa'), Exception('error generico')]
    )

    response = client.post('/inventarios/inv-1/ajustar', json={'ajuste': 3, 'usuario': 'tester'})
    assert response.status_code == 200
    assert response.get_json()['cantidad'] == 10

    response = client.post('/inventarios/inv-1/ajustar', json={'ajuste': 3, 'usuario': 'tester'})
    assert response.status_code == 404

    response = client.post('/inventarios/inv-1/ajustar', json={'ajuste': 3, 'usuario': 'tester'})
    assert response.status_code == 400

    response = client.post('/inventarios/inv-1/ajustar', json={'ajuste': 3, 'usuario': 'tester'})
    assert response.status_code == 500
    ajustar_mock.assert_called()
