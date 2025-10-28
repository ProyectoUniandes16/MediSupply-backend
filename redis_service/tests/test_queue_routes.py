"""Pruebas unitarias para las rutas de cola con Redis mockeado."""

import logging

import pytest


@pytest.fixture
def queue_service_mock(mocker):
    """Mock del redis_client usado por las rutas de queue."""
    return mocker.patch('app.routes.queue.redis_client')


def test_queue_publish_success(client, queue_service_mock, caplog):
    queue_service_mock.queue_publish.return_value = 5

    payload = {'channel': 'inventarios', 'message': {'foo': 'bar'}}
    with caplog.at_level(logging.INFO):
        response = client.post('/api/queue/publish', json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert body == {'message': 'Mensaje publicado', 'channel': 'inventarios', 'subscribers': 5}
    queue_service_mock.queue_publish.assert_called_once_with('inventarios', {'foo': 'bar'})
    assert any('inventarios' in message for message in caplog.messages)




def test_queue_channels_success(client, queue_service_mock):
    queue_service_mock.queue_channels.return_value = ['inventarios', 'productos']
    queue_service_mock.queue_num_subscribers.side_effect = [3, 1]

    response = client.get('/api/queue/channels?pattern=inv*')

    assert response.status_code == 200
    body = response.get_json()
    assert body['pattern'] == 'inv*'
    assert body['count'] == 2
    assert body['channels'] == [
        {'channel': 'inventarios', 'subscribers': 3},
        {'channel': 'productos', 'subscribers': 1},
    ]
    queue_service_mock.queue_channels.assert_called_once_with('inv*')


def test_queue_channels_error(client, queue_service_mock):
    queue_service_mock.queue_channels.side_effect = ValueError('boom')

    response = client.get('/api/queue/channels')

    assert response.status_code == 500
    assert 'boom' in response.get_json()['error']


def test_queue_subscribers_success(client, queue_service_mock):
    queue_service_mock.queue_num_subscribers.return_value = 7

    response = client.get('/api/queue/subscribers/inventarios')

    assert response.status_code == 200
    assert response.get_json() == {'channel': 'inventarios', 'subscribers': 7}
    queue_service_mock.queue_num_subscribers.assert_called_once_with('inventarios')


def test_queue_subscribers_error(client, queue_service_mock):
    queue_service_mock.queue_num_subscribers.side_effect = RuntimeError('fail')

    response = client.get('/api/queue/subscribers/a')

    assert response.status_code == 500
    assert 'fail' in response.get_json()['error']
