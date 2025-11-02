"""Pruebas unitarias para las rutas de cache con el cliente Redis mockeado."""

import pytest


@pytest.fixture
def cache_service_mock(mocker):
    """Mock del redis_client usado por las rutas de cache."""
    service_mock = mocker.patch('app.routes.cache.redis_client')
    service_mock.config = {'CACHE_DEFAULT_TTL': 3600}
    return service_mock


def test_cache_set_success(client, cache_service_mock):
    cache_service_mock.cache_set.return_value = True
    cache_service_mock.cache_ttl.return_value = 120

    payload = {'key': 'sku:1', 'value': {'foo': 'bar'}, 'ttl': 120}
    response = client.post('/api/cache/', json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert body['message'] == 'Valor guardado en cache'
    assert body['key'] == 'sku:1'
    assert body['ttl'] == 120
    cache_service_mock.cache_set.assert_called_once_with('sku:1', {'foo': 'bar'}, 120)


def test_cache_set_uses_default_ttl(client, cache_service_mock):
    cache_service_mock.cache_set.return_value = True
    cache_service_mock.cache_ttl.return_value = 3600

    payload = {'key': 'sku:2', 'value': {'foo': 'bar'}}
    response = client.post('/api/cache/', json=payload)

    assert response.status_code == 201
    assert response.get_json()['ttl'] == 3600
    cache_service_mock.cache_set.assert_called_once_with('sku:2', {'foo': 'bar'}, None)


@pytest.mark.parametrize('missing_field', ['key', 'value'])
def test_cache_set_missing_fields(client, cache_service_mock, missing_field):
    payload = {'key': 'sku:3', 'value': {'foo': 'bar'}}
    payload.pop(missing_field)

    response = client.post('/api/cache/', json=payload)

    assert response.status_code == 400
    assert 'error' in response.get_json()
    cache_service_mock.cache_set.assert_not_called()


def test_cache_set_unexpected_error(client, cache_service_mock):
    cache_service_mock.cache_set.side_effect = RuntimeError('fail')

    response = client.post('/api/cache/', json={'key': 'sku:4', 'value': 1})

    assert response.status_code == 500
    assert 'fail' in response.get_json()['error']


def test_cache_get_found(client, cache_service_mock):
    cache_service_mock.cache_get.return_value = {'foo': 'bar'}
    cache_service_mock.cache_ttl.return_value = 90

    response = client.get('/api/cache/sku:5')

    assert response.status_code == 200
    body = response.get_json()
    assert body == {'key': 'sku:5', 'value': {'foo': 'bar'}, 'ttl': 90}
    cache_service_mock.cache_get.assert_called_once_with('sku:5')


def test_cache_get_not_found(client, cache_service_mock):
    cache_service_mock.cache_get.return_value = None

    response = client.get('/api/cache/sku:missing')

    assert response.status_code == 404
    body = response.get_json()
    assert body['key'] == 'sku:missing'
    assert 'Clave no encontrada' in body['message']


def test_cache_get_error(client, cache_service_mock):
    cache_service_mock.cache_get.side_effect = ValueError('boom')

    response = client.get('/api/cache/sku:error')

    assert response.status_code == 500
    assert 'boom' in response.get_json()['error']


def test_cache_delete_found(client, cache_service_mock):
    cache_service_mock.cache_delete.return_value = 1

    response = client.delete('/api/cache/sku:6')

    assert response.status_code == 200
    assert response.get_json()['key'] == 'sku:6'


def test_cache_delete_not_found(client, cache_service_mock):
    cache_service_mock.cache_delete.return_value = 0

    response = client.delete('/api/cache/sku:7')

    assert response.status_code == 404
    assert response.get_json()['key'] == 'sku:7'


def test_cache_delete_error(client, cache_service_mock):
    cache_service_mock.cache_delete.side_effect = RuntimeError('fail')

    response = client.delete('/api/cache/sku:8')

    assert response.status_code == 500
    assert 'fail' in response.get_json()['error']


def test_cache_delete_pattern(client, cache_service_mock):
    cache_service_mock.cache_delete_pattern.return_value = 3

    response = client.delete('/api/cache/pattern/inventarios:*')

    assert response.status_code == 200
    body = response.get_json()
    assert body['pattern'] == 'inventarios:*'
    assert body['deleted_count'] == 3


def test_cache_exists(client, cache_service_mock):
    cache_service_mock.cache_exists.return_value = True

    response = client.get('/api/cache/exists/sku:9')

    assert response.status_code == 200
    assert response.get_json() == {'key': 'sku:9', 'exists': True}


def test_cache_keys(client, cache_service_mock):
    cache_service_mock.cache_keys.return_value = ['sku:1', 'sku:2']

    response = client.get('/api/cache/keys?pattern=sku:*')

    assert response.status_code == 200
    body = response.get_json()
    assert body['pattern'] == 'sku:*'
    assert body['count'] == 2
    assert body['keys'] == ['sku:1', 'sku:2']


def test_cache_keys_error(client, cache_service_mock):
    cache_service_mock.cache_keys.side_effect = RuntimeError('fail')

    response = client.get('/api/cache/keys')

    assert response.status_code == 500
    assert 'fail' in response.get_json()['error']


def test_cache_flush_requires_confirm(client, cache_service_mock):
    response = client.post('/api/cache/flush', json={'confirm': False})

    assert response.status_code == 400
    cache_service_mock.cache_flush.assert_not_called()


def test_cache_flush_success(client, cache_service_mock):
    cache_service_mock.cache_flush.return_value = True

    response = client.post('/api/cache/flush', json={'confirm': True})

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Cache limpiado completamente'
