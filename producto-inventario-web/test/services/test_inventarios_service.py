import pytest
from flask import Flask
from unittest.mock import MagicMock
import requests

from src.services.inventarios_service import InventariosService


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['INVENTARIOS_URL'] = 'http://inventarios:5009'
    app.config['REDIS_SERVICE_URL'] = 'http://redis:5011'
    return app





def test_inventarios_service_write_paths(app, mocker):
    mock_post = mocker.patch('src.services.inventarios_service.requests.post')
    mock_put = mocker.patch('src.services.inventarios_service.requests.put')
    mock_delete = mocker.patch('src.services.inventarios_service.requests.delete')

    success_post = MagicMock(status_code=201)
    success_post.json.return_value = {'id': 'inv-1'}

    conflict_post = MagicMock(status_code=409)
    conflict_post.json.return_value = {'error': 'duplicado'}

    adjust_ok = MagicMock(status_code=200)
    adjust_ok.json.return_value = {'cantidad': 11}

    adjust_bad = MagicMock(status_code=400)
    adjust_bad.json.return_value = {'error': 'negativa'}

    success_put = MagicMock(status_code=200)
    success_put.json.return_value = {'id': 'inv-1', 'cantidad': 9}

    not_found_put = MagicMock(status_code=404)
    not_found_put.json.return_value = {'error': 'no encontrado'}

    success_delete = MagicMock(status_code=200)
    success_delete.json.return_value = {'mensaje': 'ok'}

    error_delete = MagicMock(status_code=500)
    error_delete.json.return_value = {'error': 'boom'}

    with app.app_context():
        mock_post.side_effect = [success_post, conflict_post, requests.RequestException('conexion')]
        created = InventariosService.crear_inventario({'productoId': '1'})
        assert created['id'] == 'inv-1'

        with pytest.raises(Exception) as exc:
            InventariosService.crear_inventario({'productoId': '1'})
        assert 'duplicado' in str(exc.value)

        with pytest.raises(Exception) as exc:
            InventariosService.crear_inventario({'productoId': '1'})
        assert 'conexion' in str(exc.value)

        mock_put.side_effect = [success_put, not_found_put, requests.RequestException('timeout')]
        updated = InventariosService.actualizar_inventario('inv-1', {'cantidad': 9})
        assert updated['cantidad'] == 9

        with pytest.raises(Exception):
            InventariosService.actualizar_inventario('inv-1', {'cantidad': 9})

        with pytest.raises(Exception) as exc:
            InventariosService.actualizar_inventario('inv-1', {'cantidad': 9})
        assert 'timeout' in str(exc.value)

        mock_delete.side_effect = [success_delete, error_delete]
        assert InventariosService.eliminar_inventario('inv-1', 'tester') is True

        with pytest.raises(Exception):
            InventariosService.eliminar_inventario('inv-1', 'tester')

        mock_post.side_effect = [adjust_ok, adjust_bad, requests.RequestException('fallo')]
        adjusted = InventariosService.ajustar_cantidad('inv-1', 3, 'tester')
        assert adjusted['cantidad'] == 11

        with pytest.raises(Exception):
            InventariosService.ajustar_cantidad('inv-1', 3, 'tester')

        with pytest.raises(Exception) as exc:
            InventariosService.ajustar_cantidad('inv-1', 3, 'tester')
        assert 'fallo' in str(exc.value)
