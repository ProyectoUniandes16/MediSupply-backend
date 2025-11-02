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
    app.config['PRODUCTO_URL'] = 'http://productos:5008'
    return app


def test_inventarios_service_get_inventarios_by_producto(app, mocker):
    """Test get_inventarios_by_producto con cache y microservicio."""
    mock_cache = mocker.patch('src.services.inventarios_service.CacheClient')
    mock_get = mocker.patch('src.services.inventarios_service.requests.get')
    
    with app.app_context():
        # Caso 1: Cache HIT
        cache_instance = mock_cache.return_value
        cache_instance.get_inventarios_by_producto.return_value = [{'id': '1', 'cantidad': 10}]
        
        result = InventariosService.get_inventarios_by_producto('123')
        
        assert result['data']['productoId'] == '123'
        assert result['data']['total'] == 1
        assert result['data']['totalCantidad'] == 10
        assert result['data']['source'] == 'cache'
        
        # Caso 2: Cache MISS - consulta microservicio
        cache_instance.get_inventarios_by_producto.return_value = None
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'inventarios': [{'id': '2', 'cantidad': 20}]
        }
        
        result = InventariosService.get_inventarios_by_producto('456')
        
        assert result['data']['total'] == 1
        assert result['data']['totalCantidad'] == 20
        assert result['data']['source'] == 'microservice'


def test_inventarios_service_get_inventarios_microservice_error(app, mocker):
    """Test error del microservicio al obtener inventarios."""
    mock_cache = mocker.patch('src.services.inventarios_service.CacheClient')
    mock_get = mocker.patch('src.services.inventarios_service.requests.get')
    
    with app.app_context():
        cache_instance = mock_cache.return_value
        cache_instance.get_inventarios_by_producto.return_value = None
        
        # Error del microservicio
        mock_get.return_value.status_code = 500
        
        result = InventariosService.get_inventarios_by_producto('123')
        
        assert result['data']['inventarios'] == []
        assert result['data']['total'] == 0


def test_inventarios_service_get_inventarios_exception(app, mocker):
    """Test excepción al obtener inventarios del microservicio."""
    mock_cache = mocker.patch('src.services.inventarios_service.CacheClient')
    mock_get = mocker.patch('src.services.inventarios_service.requests.get')
    
    with app.app_context():
        cache_instance = mock_cache.return_value
        cache_instance.get_inventarios_by_producto.return_value = None
        
        # Excepción
        mock_get.side_effect = Exception('connection error')
        
        result = InventariosService.get_inventarios_by_producto('123')
        
        assert result['data']['inventarios'] == []


def test_inventarios_service_get_total_disponible(app, mocker):
    """Test get_total_disponible."""
    mocker.patch(
        'src.services.inventarios_service.InventariosService.get_inventarios_by_producto',
        return_value={'totalCantidad': 150}  # Sin 'data' wrapper
    )
    
    with app.app_context():
        total = InventariosService.get_total_disponible('123')
        assert total == 150


def test_inventarios_service_write_paths(app, mocker):
    mock_post = mocker.patch('src.services.inventarios_service.requests.post')
    mock_put = mocker.patch('src.services.inventarios_service.requests.put')
    mock_delete = mocker.patch('src.services.inventarios_service.requests.delete')

    success_post = MagicMock(status_code=201)
    success_post.json.return_value = {'id': 'inv-1'}

    conflict_post = MagicMock(status_code=409)
    conflict_post.json.return_value = {'error': 'duplicado'}
    conflict_post.content = b'{"error": "duplicado"}'

    adjust_ok = MagicMock(status_code=200)
    adjust_ok.json.return_value = {'cantidad': 11}

    adjust_bad = MagicMock(status_code=400)
    adjust_bad.json.return_value = {'error': 'negativa'}
    adjust_bad.content = b'{"error": "negativa"}'

    success_put = MagicMock(status_code=200)
    success_put.json.return_value = {'id': 'inv-1', 'cantidad': 9}

    not_found_put = MagicMock(status_code=404)
    not_found_put.json.return_value = {'error': 'no encontrado'}
    not_found_put.content = b'{"error": "no encontrado"}'

    success_delete = MagicMock(status_code=200)
    success_delete.json.return_value = {'mensaje': 'ok'}

    error_delete = MagicMock(status_code=500)
    error_delete.json.return_value = {'error': 'boom'}
    error_delete.content = b'{"error": "boom"}'

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


def test_inventarios_service_crear_inventario_sin_content(app, mocker):
    """Test crear inventario cuando la respuesta no tiene content."""
    mock_post = mocker.patch('src.services.inventarios_service.requests.post')
    
    error_response = MagicMock(status_code=400)
    error_response.content = None
    
    with app.app_context():
        mock_post.return_value = error_response
        
        with pytest.raises(Exception) as exc:
            InventariosService.crear_inventario({'productoId': '1'})
        assert 'Error 400' in str(exc.value)


def test_inventarios_service_actualizar_inventario_sin_content(app, mocker):
    """Test actualizar inventario cuando la respuesta no tiene content."""
    mock_put = mocker.patch('src.services.inventarios_service.requests.put')
    
    error_response = MagicMock(status_code=400)
    error_response.content = None
    
    with app.app_context():
        mock_put.return_value = error_response
        
        with pytest.raises(Exception) as exc:
            InventariosService.actualizar_inventario('inv-1', {'cantidad': 10})
        assert 'Error 400' in str(exc.value)


def test_inventarios_service_eliminar_inventario_sin_content(app, mocker):
    """Test eliminar inventario cuando la respuesta no tiene content."""
    mock_delete = mocker.patch('src.services.inventarios_service.requests.delete')
    
    error_response = MagicMock(status_code=400)
    error_response.content = None
    
    with app.app_context():
        mock_delete.return_value = error_response
        
        with pytest.raises(Exception) as exc:
            InventariosService.eliminar_inventario('inv-1')
        assert 'Error 400' in str(exc.value)


def test_inventarios_service_ajustar_cantidad_sin_content(app, mocker):
    """Test ajustar cantidad cuando la respuesta no tiene content."""
    mock_post = mocker.patch('src.services.inventarios_service.requests.post')
    
    error_response = MagicMock(status_code=400)
    error_response.content = None
    
    with app.app_context():
        mock_post.return_value = error_response
        
        with pytest.raises(Exception) as exc:
            InventariosService.ajustar_cantidad('inv-1', 5)
        assert 'Error 400' in str(exc.value)


def test_inventarios_service_get_productos_con_inventarios_cache_hit(app, mocker):
    """Test get_productos_con_inventarios con cache HIT."""
    mock_cache = mocker.patch('src.services.inventarios_service.CacheClient')
    
    with app.app_context():
        cache_instance = mock_cache.return_value
        cached_data = [
            {'id': 1, 'nombre': 'Producto 1', 'inventarios': [{'cantidad': 10}]}
        ]
        cache_instance.get_generic.return_value = cached_data
        
        result = InventariosService.get_productos_con_inventarios()
        
        assert result['data'] == cached_data
        assert result['total'] == 1
        assert result['source'] == 'cache'


def test_inventarios_service_get_productos_con_inventarios_cache_miss(app, mocker):
    """Test get_productos_con_inventarios con cache MISS."""
    mock_cache = mocker.patch('src.services.inventarios_service.CacheClient')
    mock_get = mocker.patch('src.services.inventarios_service.requests.get')
    
    with app.app_context():
        cache_instance = mock_cache.return_value
        cache_instance.get_generic.return_value = None
        cache_instance.get_inventarios_by_producto.return_value = [{'cantidad': 15}]
        
        # Mock respuesta de productos
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'productos': [{'id': 1, 'nombre': 'Test'}]
        }
        mock_get.return_value.raise_for_status = lambda: None
        
        result = InventariosService.get_productos_con_inventarios()
        
        assert result['total'] == 1
        assert result['source'] == 'microservices'
        assert result['data'][0]['totalInventario'] == 15

