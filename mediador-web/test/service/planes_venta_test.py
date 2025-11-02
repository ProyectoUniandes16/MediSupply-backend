import pytest
from unittest.mock import patch, MagicMock
import requests
from flask import Flask
from src.services.vendedores import (
    crear_plan_venta_externo,
    listar_planes_venta_externo,
    obtener_plan_venta_externo,
    VendedorServiceError
)


@pytest.fixture
def app():
    """Crear aplicación Flask para contexto"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


# ==================== Tests para crear_plan_venta_externo ====================

@patch('src.services.vendedores.requests.post')
def test_crear_plan_venta_exito(mock_post, app):
    """Test de creación exitosa de plan de venta"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'plan-123',
            'nombre_plan': 'Plan Q1 2025',
            'operacion': 'crear',
            'mensaje': 'Plan de venta creado exitosamente'
        }
        mock_post.return_value = mock_response
        
        datos_plan = {
            'nombre_plan': 'Plan Q1 2025',
            'gerente_id': 'gerente-123',
            'vendedores_ids': ['vendedor-1', 'vendedor-2'],
            'periodo': '2025-01',
            'meta_ingresos': 50000.00,
            'meta_visitas': 100,
            'meta_clientes_nuevos': 20
        }
        
        resultado = crear_plan_venta_externo(datos_plan)
        
        assert resultado['id'] == 'plan-123'
        assert resultado['operacion'] == 'crear'
        mock_post.assert_called_once()


def test_crear_plan_venta_sin_datos(app):
    """Test de error cuando no se proporcionan datos"""
    with app.app_context():
        with pytest.raises(VendedorServiceError) as excinfo:
            crear_plan_venta_externo(None)
        
        assert excinfo.value.status_code == 400
        assert 'No se proporcionaron datos' in str(excinfo.value.message)


def test_crear_plan_venta_campos_faltantes(app):
    """Test de error cuando faltan campos obligatorios"""
    with app.app_context():
        datos_plan = {
            'nombre_plan': 'Plan Test'
            # Faltan campos obligatorios
        }
        
        with pytest.raises(VendedorServiceError) as excinfo:
            crear_plan_venta_externo(datos_plan)
        
        assert excinfo.value.status_code == 400
        assert 'Campos faltantes' in str(excinfo.value.message)


@patch('src.services.vendedores.requests.post')
def test_crear_plan_venta_error_http(mock_post, app):
    """Test de error HTTP del microservicio"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_response.json.return_value = {
            'error': 'Vendedor no encontrado',
            'codigo': 'VENDEDOR_NO_ENCONTRADO'
        }
        
        # Crear HTTPError con response
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response
        
        datos_plan = {
            'nombre_plan': 'Plan Test',
            'gerente_id': 'gerente-123',
            'vendedores_ids': ['vendedor-inexistente'],
            'periodo': '2025-01',
            'meta_ingresos': 50000,
            'meta_visitas': 100,
            'meta_clientes_nuevos': 20
        }
        
        with pytest.raises(VendedorServiceError) as excinfo:
            crear_plan_venta_externo(datos_plan)
        
        assert excinfo.value.status_code == 404


@patch('src.services.vendedores.requests.post')
def test_crear_plan_venta_error_conexion(mock_post, app):
    """Test de error de conexión con microservicio"""
    with app.app_context():
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        datos_plan = {
            'nombre_plan': 'Plan Test',
            'gerente_id': 'gerente-123',
            'vendedores_ids': ['vendedor-1'],
            'periodo': '2025-01',
            'meta_ingresos': 50000,
            'meta_visitas': 100,
            'meta_clientes_nuevos': 20
        }
        
        with pytest.raises(VendedorServiceError) as excinfo:
            crear_plan_venta_externo(datos_plan)
        
        assert excinfo.value.status_code == 503
        assert 'ERROR_CONEXION' in str(excinfo.value.message)


# ==================== Tests para listar_planes_venta_externo ====================

@patch('src.services.vendedores.requests.get')
def test_listar_planes_venta_exito(mock_get, app):
    """Test de listado exitoso de planes de venta"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': 'plan-1', 'nombre_plan': 'Plan Q1 2025'},
                {'id': 'plan-2', 'nombre_plan': 'Plan Q2 2025'}
            ],
            'total': 2,
            'page': 1,
            'size': 10,
            'pages': 1
        }
        mock_get.return_value = mock_response
        
        resultado = listar_planes_venta_externo(page=1, size=10)
        
        assert len(resultado['items']) == 2
        assert resultado['total'] == 2
        mock_get.assert_called_once()


@patch('src.services.vendedores.requests.get')
def test_listar_planes_venta_con_filtros(mock_get, app):
    """Test de listado con filtros aplicados"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': 'plan-1', 'nombre_plan': 'Plan Q1 2025', 'periodo': '2025-01'}
            ],
            'total': 1,
            'page': 1,
            'size': 10,
            'pages': 1
        }
        mock_get.return_value = mock_response
        
        resultado = listar_planes_venta_externo(
            vendedor_id='v1',
            periodo='2025-01',
            estado='activo',
            nombre_plan='Q1',
            page=1,
            size=10
        )
        
        assert len(resultado['items']) == 1
        assert resultado['items'][0]['periodo'] == '2025-01'
        
        # Verificar que se llamó con los parámetros correctos
        call_args = mock_get.call_args
        assert call_args[1]['params']['vendedor_id'] == 'v1'
        assert call_args[1]['params']['periodo'] == '2025-01'
        assert call_args[1]['params']['estado'] == 'activo'
        assert call_args[1]['params']['nombre_plan'] == 'Q1'


@patch('src.services.vendedores.requests.get')
def test_listar_planes_venta_error_http(mock_get, app):
    """Test de error HTTP al listar planes"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_response.json.return_value = {
            'error': 'Error interno',
            'codigo': 'ERROR_INTERNO'
        }
        
        # Crear HTTPError con response
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        
        with pytest.raises(VendedorServiceError) as excinfo:
            listar_planes_venta_externo()
        
        assert excinfo.value.status_code == 500


@patch('src.services.vendedores.requests.get')
def test_listar_planes_venta_error_conexion(mock_get, app):
    """Test de error de conexión al listar"""
    with app.app_context():
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(VendedorServiceError) as excinfo:
            listar_planes_venta_externo()
        
        assert excinfo.value.status_code == 503


# ==================== Tests para obtener_plan_venta_externo ====================

@patch('src.services.vendedores.requests.get')
def test_obtener_plan_venta_exito(mock_get, app):
    """Test de obtención exitosa de plan de venta por ID"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'plan-123',
            'nombre_plan': 'Plan Q1 2025',
            'periodo': '2025-01',
            'estado': 'activo'
        }
        mock_get.return_value = mock_response
        
        resultado = obtener_plan_venta_externo('plan-123')
        
        assert resultado['id'] == 'plan-123'
        assert resultado['nombre_plan'] == 'Plan Q1 2025'
        mock_get.assert_called_once()


@patch('src.services.vendedores.requests.get')
def test_obtener_plan_venta_no_encontrado(mock_get, app):
    """Test cuando plan de venta no existe"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_response.json.return_value = {
            'error': 'Plan de venta no encontrado',
            'codigo': 'PLAN_NO_ENCONTRADO'
        }
        
        # Crear HTTPError con response
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_plan_venta_externo('plan-inexistente')
        
        assert excinfo.value.status_code == 404


@patch('src.services.vendedores.requests.get')
def test_obtener_plan_venta_error_conexion(mock_get, app):
    """Test de error de conexión al obtener plan"""
    with app.app_context():
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(VendedorServiceError) as excinfo:
            obtener_plan_venta_externo('plan-123')
        
        assert excinfo.value.status_code == 503
        assert 'ERROR_CONEXION' in str(excinfo.value.message)
