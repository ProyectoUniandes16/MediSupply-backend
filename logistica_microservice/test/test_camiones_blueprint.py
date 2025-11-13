import pytest
import json


def test_crear_camion_endpoint_exito(client, access_token):
    """Test de creación de camión a través del endpoint"""
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    
    # Crear datos necesarios
    zona = crear_zona({
        'nombre': 'Zona Camion Endpoint',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    })
    
    bodega = crear_bodega({
        'nombre': 'Bodega Camion Endpoint',
        'ubicacion': 'Ubicacion',
        'zona_id': zona['id']
    })
    
    tipo = crear_tipo_camion({
        'nombre': 'Refrigerado Endpoint'
    })
    
    data = {
        'placa': 'BBB222',
        'capacidad_kg': 4000.0,
        'capacidad_m3': 40.0,
        'bodega_id': bodega['id'],
        'tipo_camion_id': tipo['id']
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/camion',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['placa'] == 'BBB222'
    assert 'tipo_camion' in json_data


def test_listar_camiones_por_bodega_endpoint(client, access_token):
    """Test del endpoint para listar camiones por bodega"""
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    from src.services.camion_service import crear_camion
    
    # Crear datos
    zona = crear_zona({
        'nombre': 'Zona Lista Endpoint',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    })
    
    bodega = crear_bodega({
        'nombre': 'Bodega Lista Endpoint',
        'ubicacion': 'Ubicacion',
        'zona_id': zona['id']
    })
    
    tipo = crear_tipo_camion({
        'nombre': 'Sin Refrig Endpoint'
    })
    
    # Crear camiones
    crear_camion({
        'placa': 'CCC333',
        'capacidad_kg': 2000.0,
        'capacidad_m3': 20.0,
        'bodega_id': bodega['id'],
        'tipo_camion_id': tipo['id']
    })
    
    crear_camion({
        'placa': 'DDD444',
        'capacidad_kg': 2500.0,
        'capacidad_m3': 25.0,
        'bodega_id': bodega['id'],
        'tipo_camion_id': tipo['id']
    })
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(f'/bodega/{bodega["id"]}/camiones', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    
    assert 'camiones' in json_data
    assert json_data['total'] == 2
    assert json_data['bodega_nombre'] == 'Bodega Lista Endpoint'


def test_actualizar_estado_camion_endpoint(client, access_token):
    """Test del endpoint para actualizar estado de camión"""
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    from src.services.camion_service import crear_camion
    
    # Crear datos
    zona = crear_zona({
        'nombre': 'Zona Estado Endpoint',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    })
    
    bodega = crear_bodega({
        'nombre': 'Bodega Estado Endpoint',
        'ubicacion': 'Ubicacion',
        'zona_id': zona['id']
    })
    
    tipo = crear_tipo_camion({
        'nombre': 'Mixto Estado Endpoint'
    })
    
    camion = crear_camion({
        'placa': 'EEE555',
        'capacidad_kg': 3500.0,
        'capacidad_m3': 35.0,
        'bodega_id': bodega['id'],
        'tipo_camion_id': tipo['id']
    })
    
    data = {'estado': 'mantenimiento'}
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.patch(f'/camion/{camion["id"]}/estado',
                           data=json.dumps(data),
                           headers=headers,
                           content_type='application/json')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['estado'] == 'mantenimiento'


def test_inicializar_tipos_camion_endpoint(client, access_token):
    """Test del endpoint para inicializar tipos de camión"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/tipo-camion/inicializar', headers=headers)
    
    assert response.status_code == 201
    json_data = response.get_json()
    
    assert 'message' in json_data
    assert 'tipos_creados' in json_data
