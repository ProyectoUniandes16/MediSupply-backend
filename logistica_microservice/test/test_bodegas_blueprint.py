import pytest
import json


def test_crear_bodega_endpoint_exito(client, access_token):
    """Test de creación exitosa de bodega a través del endpoint"""
    # Crear una zona primero
    zona_data = {
        'nombre': 'Zona Para Bodega',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    zona_response = client.post('/zona',
                               data=json.dumps(zona_data),
                               headers=headers,
                               content_type='application/json')
    
    zona_id = zona_response.get_json()['id']
    
    bodega_data = {
        'nombre': 'Bodega Principal',
        'ubicacion': 'Calle 123 #45-67',
        'zona_id': zona_id
    }
    
    response = client.post('/bodega',
                          data=json.dumps(bodega_data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['nombre'] == 'Bodega Principal'
    assert 'id' in json_data


# Test eliminado: El microservicio de logística no requiere autenticación
# def test_crear_bodega_sin_token(client):


def test_crear_bodega_error_validacion(client, access_token):
    """Test de error de validación al crear bodega"""
    data = {
        'nombre': 'Bodega Sin Ubicacion'
        # Faltan campos requeridos
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/bodega',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 400


def test_listar_bodegas_endpoint(client, access_token):
    """Test de listado de bodegas a través del endpoint"""
    # Crear una zona
    zona_data = {
        'nombre': 'Zona Para Listar',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    zona_response = client.post('/zona',
                               data=json.dumps(zona_data),
                               headers=headers,
                               content_type='application/json')
    
    zona_id = zona_response.get_json()['id']
    
    # Crear bodegas
    bodega1 = {
        'nombre': 'Bodega 1',
        'ubicacion': 'Ubicacion 1',
        'zona_id': zona_id
    }
    bodega2 = {
        'nombre': 'Bodega 2',
        'ubicacion': 'Ubicacion 2',
        'zona_id': zona_id
    }
    
    client.post('/bodega', data=json.dumps(bodega1), headers=headers, content_type='application/json')
    client.post('/bodega', data=json.dumps(bodega2), headers=headers, content_type='application/json')
    
    response = client.get('/bodega', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'data' in json_data
    assert json_data['total'] == 2


# Test eliminado: El microservicio de logística no requiere autenticación
# def test_listar_bodegas_sin_token(client):


def test_obtener_bodega_endpoint(client, access_token):
    """Test de obtención de bodega por ID"""
    # Crear una zona
    zona_data = {
        'nombre': 'Zona Para Obtener Bodega',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    zona_response = client.post('/zona',
                               data=json.dumps(zona_data),
                               headers=headers,
                               content_type='application/json')
    
    zona_id = zona_response.get_json()['id']
    
    # Crear bodega
    bodega_data = {
        'nombre': 'Bodega Para Obtener',
        'ubicacion': 'Ubicacion Test',
        'zona_id': zona_id
    }
    
    create_response = client.post('/bodega',
                                 data=json.dumps(bodega_data),
                                 headers=headers,
                                 content_type='application/json')
    
    bodega_id = create_response.get_json()['id']
    
    response = client.get(f'/bodega/{bodega_id}', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['id'] == bodega_id
    assert json_data['nombre'] == 'Bodega Para Obtener'


def test_obtener_bodega_no_encontrada(client, access_token):
    """Test de obtención de bodega no existente"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/bodega/id-inexistente', headers=headers)
    
    assert response.status_code == 404
