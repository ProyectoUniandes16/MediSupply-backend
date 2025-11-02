import pytest
from unittest.mock import patch
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.vendedores import vendedores_bp
from src.services.vendedores import VendedorServiceError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    JWTManager(app)
    app.register_blueprint(vendedores_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity='user123')


# ==================== Tests para POST /planes-venta ====================

@patch('src.blueprints.vendedores.crear_plan_venta_externo')
def test_crear_plan_venta_exito(mock_crear_plan, client, access_token):
    """Test de creación exitosa de plan de venta"""
    mock_crear_plan.return_value = {
        'id': 'plan-123',
        'nombre_plan': 'Plan Q1 2025',
        'operacion': 'crear',
        'mensaje': 'Plan de venta creado exitosamente'
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    data = {
        'nombre_plan': 'Plan Q1 2025',
        'gerente_id': 'gerente-123',
        'vendedores_ids': ['vendedor-1', 'vendedor-2'],
        'periodo': '2025-01',
        'meta_ingresos': 50000.00,
        'meta_visitas': 100,
        'meta_clientes_nuevos': 20
    }
    response = client.post('/planes-venta', json=data, headers=headers)

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['id'] == 'plan-123'
    assert json_data['operacion'] == 'crear'
    mock_crear_plan.assert_called_once_with(data)


@patch('src.blueprints.vendedores.crear_plan_venta_externo')
def test_crear_plan_venta_actualizar(mock_crear_plan, client, access_token):
    """Test de actualización de plan de venta (operación = actualizar)"""
    mock_crear_plan.return_value = {
        'id': 'plan-123',
        'nombre_plan': 'Plan Q1 2025 Actualizado',
        'operacion': 'actualizar',
        'mensaje': 'Plan de venta actualizado exitosamente'
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    data = {
        'plan_id': 'plan-123',
        'nombre_plan': 'Plan Q1 2025 Actualizado',
        'gerente_id': 'gerente-123',
        'vendedores_ids': ['vendedor-1'],
        'periodo': '2025-01',
        'meta_ingresos': 60000.00,
        'meta_visitas': 120,
        'meta_clientes_nuevos': 25
    }
    response = client.post('/planes-venta', json=data, headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['operacion'] == 'actualizar'


@patch('src.blueprints.vendedores.crear_plan_venta_externo')
def test_crear_plan_venta_error_validacion(mock_crear_plan, client, access_token):
    """Test de error de validación al crear plan de venta"""
    error = VendedorServiceError({
        'error': 'Campos faltantes',
        'codigo': 'CAMPOS_FALTANTES'
    }, 400)
    mock_crear_plan.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/planes-venta', json={}, headers=headers)

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data


@patch('src.blueprints.vendedores.crear_plan_venta_externo')
def test_crear_plan_venta_vendedor_no_encontrado(mock_crear_plan, client, access_token):
    """Test de error cuando vendedor no existe"""
    error = VendedorServiceError({
        'error': 'Vendedor no encontrado',
        'codigo': 'VENDEDOR_NO_ENCONTRADO'
    }, 404)
    mock_crear_plan.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    data = {
        'nombre_plan': 'Plan Test',
        'vendedores_ids': ['vendedor-inexistente']
    }
    response = client.post('/planes-venta', json=data, headers=headers)

    assert response.status_code == 404


def test_crear_plan_venta_sin_token(client):
    """Test sin autorización debe responder 401"""
    response = client.post('/planes-venta', json={'nombre_plan': 'Plan Test'})
    assert response.status_code == 401


# ==================== Tests para GET /planes-venta ====================

@patch('src.blueprints.vendedores.listar_planes_venta_externo')
def test_listar_planes_venta_exito(mock_listar, client, access_token):
    """Test de listado exitoso de planes de venta"""
    mock_listar.return_value = {
        'items': [
            {
                'id': 'plan-1',
                'nombre_plan': 'Plan Q1 2025',
                'periodo': '2025-01',
                'estado': 'activo'
            },
            {
                'id': 'plan-2',
                'nombre_plan': 'Plan Q2 2025',
                'periodo': '2025-04',
                'estado': 'activo'
            }
        ],
        'total': 2,
        'page': 1,
        'size': 10,
        'pages': 1
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/planes-venta?page=1&size=10', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['items']) == 2
    assert json_data['total'] == 2
    mock_listar.assert_called_once()


@patch('src.blueprints.vendedores.listar_planes_venta_externo')
def test_listar_planes_venta_con_filtros(mock_listar, client, access_token):
    """Test de listado con filtros"""
    mock_listar.return_value = {
        'items': [
            {
                'id': 'plan-1',
                'nombre_plan': 'Plan Q1 2025',
                'periodo': '2025-01',
                'estado': 'activo'
            }
        ],
        'total': 1,
        'page': 1,
        'size': 10,
        'pages': 1
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/planes-venta?vendedor_id=v1&periodo=2025-01&estado=activo&nombre_plan=Q1',
        headers=headers
    )

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['total'] == 1
    mock_listar.assert_called_once_with(
        vendedor_id='v1',
        periodo='2025-01',
        estado='activo',
        nombre_plan='Q1',
        page=1,
        size=10
    )


@patch('src.blueprints.vendedores.listar_planes_venta_externo')
def test_listar_planes_venta_paginacion_invalida(mock_listar, client, access_token):
    """Test de validación de parámetros de paginación"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Page < 1
    response = client.get('/planes-venta?page=0', headers=headers)
    assert response.status_code == 400
    
    # Size > 100
    response = client.get('/planes-venta?size=150', headers=headers)
    assert response.status_code == 400


@patch('src.blueprints.vendedores.listar_planes_venta_externo')
def test_listar_planes_venta_error_servicio(mock_listar, client, access_token):
    """Test de error del servicio al listar"""
    error = VendedorServiceError({
        'error': 'Error de conexión',
        'codigo': 'ERROR_CONEXION'
    }, 503)
    mock_listar.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/planes-venta', headers=headers)

    assert response.status_code == 503


def test_listar_planes_venta_sin_token(client):
    """Test sin autorización debe responder 401"""
    response = client.get('/planes-venta')
    assert response.status_code == 401


# ==================== Tests para GET /planes-venta/<plan_id> ====================

@patch('src.blueprints.vendedores.obtener_plan_venta_externo')
def test_obtener_plan_venta_exito(mock_obtener, client, access_token):
    """Test de obtención exitosa de plan de venta por ID"""
    mock_obtener.return_value = {
        'id': 'plan-123',
        'nombre_plan': 'Plan Q1 2025',
        'gerente_id': 'gerente-1',
        'periodo': '2025-01',
        'meta_ingresos': 50000.00,
        'meta_visitas': 100,
        'meta_clientes_nuevos': 20,
        'estado': 'activo',
        'vendedores': [
            {'id': 'v1', 'nombre': 'Juan', 'apellidos': 'Perez'}
        ]
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/planes-venta/plan-123', headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['data']['id'] == 'plan-123'
    assert json_data['data']['nombre_plan'] == 'Plan Q1 2025'
    mock_obtener.assert_called_once_with('plan-123')


@patch('src.blueprints.vendedores.obtener_plan_venta_externo')
def test_obtener_plan_venta_no_encontrado(mock_obtener, client, access_token):
    """Test cuando plan de venta no existe"""
    error = VendedorServiceError({
        'error': 'Plan de venta no encontrado',
        'codigo': 'PLAN_NO_ENCONTRADO'
    }, 404)
    mock_obtener.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/planes-venta/plan-inexistente', headers=headers)

    assert response.status_code == 404
    json_data = response.get_json()
    assert 'error' in json_data


def test_obtener_plan_venta_sin_token(client):
    """Test sin autorización debe responder 401"""
    response = client.get('/planes-venta/plan-123')
    assert response.status_code == 401
