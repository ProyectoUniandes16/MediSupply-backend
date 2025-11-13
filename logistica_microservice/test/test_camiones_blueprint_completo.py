import pytest
import json
from unittest.mock import patch


def test_listar_camiones_endpoint(client, access_token):
    """Test del endpoint para listar camiones"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/camion', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'data' in json_data
    assert 'total' in json_data


def test_crear_camion_error_validacion(client, access_token):
    """Test de error de validación al crear camión"""
    data = {'placa': 'TEST'}  # Faltan campos
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/camion',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 400


def test_obtener_camion_endpoint(client, access_token):
    """Test del endpoint para obtener camión por ID"""
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    from src.services.camion_service import crear_camion
    
    zona = crear_zona({
        'nombre': 'Zona GET',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    })
    
    bodega = crear_bodega({
        'nombre': 'Bodega GET',
        'ubicacion': 'Ubicacion',
        'zona_id': zona['id']
    })
    
    tipo = crear_tipo_camion({'nombre': 'Tipo GET'})
    
    camion = crear_camion({
        'placa': 'GET123',
        'capacidad_kg': 2000.0,
        'capacidad_m3': 20.0,
        'bodega_id': bodega['id'],
        'tipo_camion_id': tipo['id']
    })
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(f'/camion/{camion["id"]}', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['id'] == camion['id']


def test_obtener_camion_no_encontrado(client, access_token):
    """Test de obtener camión no encontrado"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/camion/id-inexistente', headers=headers)
    
    assert response.status_code == 404


def test_actualizar_estado_sin_campo(client, access_token):
    """Test de actualizar estado sin campo estado"""
    data = {}
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.patch('/camion/test-id/estado',
                           data=json.dumps(data),
                           headers=headers,
                           content_type='application/json')
    
    assert response.status_code == 400


def test_actualizar_estado_camion_no_encontrado(client, access_token):
    """Test de actualizar estado de camión no encontrado"""
    data = {'estado': 'disponible'}
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.patch('/camion/id-inexistente/estado',
                           data=json.dumps(data),
                           headers=headers,
                           content_type='application/json')
    
    assert response.status_code == 404


def test_crear_camion_exception_generica(client, access_token):
    """Test de manejo de excepción genérica al crear"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.camiones.crear_camion') as mock_crear:
        mock_crear.side_effect = Exception('Error inesperado')
        
        data = {
            'placa': 'TEST',
            'capacidad_kg': 1000.0,
            'capacidad_m3': 10.0,
            'bodega_id': 'test',
            'tipo_camion_id': 'test'
        }
        
        response = client.post('/camion',
                              data=json.dumps(data),
                              headers=headers,
                              content_type='application/json')
        
        assert response.status_code == 500


def test_listar_camiones_exception_generica(client, access_token):
    """Test de excepción en listar camiones"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.camiones.listar_camiones') as mock_listar:
        mock_listar.side_effect = Exception('Error inesperado')
        
        response = client.get('/camion', headers=headers)
        assert response.status_code == 500


def test_obtener_camion_exception_generica(client, access_token):
    """Test de excepción en obtener camión"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.camiones.obtener_camion') as mock_obtener:
        mock_obtener.side_effect = Exception('Error inesperado')
        
        response = client.get('/camion/test-id', headers=headers)
        assert response.status_code == 500


def test_listar_camiones_bodega_exception_generica(client, access_token):
    """Test de excepción en listar camiones por bodega"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.camiones.listar_camiones_por_bodega') as mock_listar:
        mock_listar.side_effect = Exception('Error inesperado')
        
        response = client.get('/bodega/test-id/camiones', headers=headers)
        assert response.status_code == 500


def test_actualizar_estado_exception_generica(client, access_token):
    """Test de excepción en actualizar estado"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.camiones.actualizar_estado_camion') as mock_actualizar:
        mock_actualizar.side_effect = Exception('Error inesperado')
        
        data = {'estado': 'disponible'}
        response = client.patch('/camion/test-id/estado',
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        
        assert response.status_code == 500
