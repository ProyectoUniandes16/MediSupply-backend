import pytest
import json
from src.services.zona_service import crear_zona, obtener_zona_detallada
from src.services.bodega_service import crear_bodega
from src.services.tipo_camion_service import crear_tipo_camion
from src.services.camion_service import crear_camion


def test_obtener_zona_detallada_exito(app):
    """Test de obtención de zona detallada con bodegas y camiones"""
    with app.app_context():
        # Crear zona
        zona_data = {
            'nombre': 'Zona Detallada Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona = crear_zona(zona_data)
        
        # Crear bodega
        bodega_data = {
            'nombre': 'Bodega Detallada',
            'ubicacion': 'Ubicacion Detallada',
            'zona_id': zona['id']
        }
        bodega = crear_bodega(bodega_data)
        
        # Crear tipo de camión
        tipo_data = {
            'nombre': 'Refrigerado Test',
            'descripcion': 'Camión refrigerado'
        }
        tipo = crear_tipo_camion(tipo_data)
        
        # Crear camión
        camion_data = {
            'placa': 'ZZZ999',
            'capacidad_kg': 5000.0,
            'capacidad_m3': 50.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        }
        crear_camion(camion_data)
        
        # Obtener zona detallada
        result = obtener_zona_detallada(zona['id'])
        
        assert result['id'] == zona['id']
        assert result['nombre'] == 'Zona Detallada Test'
        assert 'bodegas' in result
        assert len(result['bodegas']) == 1
        assert result['bodegas'][0]['nombre'] == 'Bodega Detallada'
        assert 'camiones' in result['bodegas'][0]
        assert len(result['bodegas'][0]['camiones']) == 1
        assert result['bodegas'][0]['camiones'][0]['placa'] == 'ZZZ999'


def test_obtener_zona_detallada_endpoint(client, access_token):
    """Test del endpoint de zona detallada"""
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    from src.services.camion_service import crear_camion
    
    # Crear zona
    zona = crear_zona({
        'nombre': 'Zona Endpoint Test',
        'latitud_maxima': 10.0,
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    })
    
    # Crear bodega
    bodega = crear_bodega({
        'nombre': 'Bodega Endpoint',
        'ubicacion': 'Ubicacion Endpoint',
        'zona_id': zona['id']
    })
    
    # Crear tipo
    tipo = crear_tipo_camion({
        'nombre': 'Mixto Endpoint'
    })
    
    # Crear camión
    crear_camion({
        'placa': 'AAA111',
        'capacidad_kg': 3000.0,
        'capacidad_m3': 30.0,
        'bodega_id': bodega['id'],
        'tipo_camion_id': tipo['id']
    })
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(f'/zona/{zona["id"]}/detalle', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    
    assert json_data['id'] == zona['id']
    assert 'bodegas' in json_data
    assert len(json_data['bodegas']) == 1
    assert 'camiones' in json_data['bodegas'][0]
