import pytest
import json


def test_crear_zona_endpoint_exito(client, access_token):
    """Test de creación exitosa de zona a través del endpoint"""
    data = {
        'nombre': 'Zona Norte',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/zona', 
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['nombre'] == 'Zona Norte'
    assert 'id' in json_data


def test_crear_zona_error_validacion(client, access_token):
    """Test de error de validación al crear zona"""
    data = {
        'nombre': 'Zona Invalida'
        # Faltan campos requeridos
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/zona',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 400


def test_listar_zonas_endpoint(client, access_token):
    """Test de listado de zonas a través del endpoint"""
    # Crear algunas zonas primero
    data1 = {
        'nombre': 'Zona 1',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    data2 = {
        'nombre': 'Zona 2',
        'latitud_maxima': 15.0,
        'latitud_minima': 10.0,
        'longitud_maxima': -65.0,
        'longitud_minima': -70.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    client.post('/zona', data=json.dumps(data1), headers=headers, content_type='application/json')
    client.post('/zona', data=json.dumps(data2), headers=headers, content_type='application/json')
    
    response = client.get('/zona', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'data' in json_data
    assert json_data['total'] == 2


def test_obtener_zona_endpoint(client, access_token):
    """Test de obtención de zona por ID"""
    # Crear una zona primero
    data = {
        'nombre': 'Zona Test',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    create_response = client.post('/zona',
                                  data=json.dumps(data),
                                  headers=headers,
                                  content_type='application/json')
    
    zona_id = create_response.get_json()['id']
    
    response = client.get(f'/zona/{zona_id}', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['id'] == zona_id
    assert json_data['nombre'] == 'Zona Test'


def test_obtener_zona_no_encontrada(client, access_token):
    """Test de obtención de zona no existente"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/zona/id-inexistente', headers=headers)
    
    assert response.status_code == 404


def test_listar_zonas_con_bodegas_endpoint(client, access_token):
    """Test de listado de zonas con sus bodegas"""
    # Crear una zona
    zona_data = {
        'nombre': 'Zona Con Bodegas',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    create_response = client.post('/zona',
                                  data=json.dumps(zona_data),
                                  headers=headers,
                                  content_type='application/json')
    
    zona_id = create_response.get_json()['id']
    
    # Crear una bodega en esa zona
    bodega_data = {
        'nombre': 'Bodega Test',
        'ubicacion': 'Ubicacion Test',
        'zona_id': zona_id
    }
    
    client.post('/bodega',
               data=json.dumps(bodega_data),
               headers=headers,
               content_type='application/json')
    
    response = client.get('/zona-con-bodegas', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'data' in json_data
    assert len(json_data['data']) > 0
    assert 'bodegas' in json_data['data'][0]
