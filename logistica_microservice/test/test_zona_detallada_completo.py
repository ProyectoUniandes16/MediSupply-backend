import pytest
from src.services.zona_service import ZonaServiceError
from src.services.bodega_service import crear_bodega
from src.services.zona_service import crear_zona
from src import db
from unittest.mock import patch


def test_obtener_zona_detallada_no_encontrada(app):
    """Test de obtener zona detallada que no existe"""
    from src.services.zona_service import obtener_zona_detallada
    
    with app.app_context():
        with pytest.raises(ZonaServiceError) as excinfo:
            obtener_zona_detallada('id-inexistente')
        
        assert excinfo.value.status_code == 404


def test_obtener_zona_detallada_sin_bodegas(app):
    """Test de zona detallada sin bodegas asociadas"""
    from src.services.zona_service import obtener_zona_detallada
    
    with app.app_context():
        zona = crear_zona({
            'nombre': 'Zona Sin Bodegas',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        result = obtener_zona_detallada(zona['id'])
        
        assert result['id'] == zona['id']
        assert 'bodegas' in result
        assert len(result['bodegas']) == 0


def test_obtener_zona_detallada_endpoint_no_encontrada(client, access_token):
    """Test del endpoint de zona detallada no encontrada"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/zona/id-inexistente/detalle', headers=headers)
    
    assert response.status_code == 404


def test_obtener_zona_detallada_exception_generica(client, access_token):
    """Test de manejo de excepción genérica"""
    from unittest.mock import patch
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.zonas.obtener_zona_detallada') as mock_obtener:
        mock_obtener.side_effect = Exception('Error inesperado')
        
        response = client.get('/zona/test-id/detalle', headers=headers)
        assert response.status_code == 500


def test_bodega_to_dict_with_camiones(app):
    """Test del método to_dict_with_camiones de Bodega"""
    from src.models.bodega import Bodega
    from src.models.camion import Camion
    from src.models.tipo_camion import TipoCamion
    
    with app.app_context():
        # Crear zona
        zona = crear_zona({
            'nombre': 'Zona Bodega Camiones',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        # Crear bodega
        bodega_data = crear_bodega({
            'nombre': 'Bodega Camiones',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        # Obtener bodega del DB
        bodega_db = Bodega.query.filter_by(id=bodega_data['id']).first()
        
        # Crear tipo y camión
        tipo = TipoCamion(nombre='Tipo Test')
        db.session.add(tipo)
        db.session.commit()
        
        camion = Camion(
            placa='TEST999',
            capacidad_kg=1000.0,
            capacidad_m3=10.0,
            bodega_id=bodega_db.id,
            tipo_camion_id=tipo.id
        )
        db.session.add(camion)
        db.session.commit()
        
        # Probar serialización
        bodega_dict = bodega_db.to_dict_with_camiones()
        
        assert 'camiones' in bodega_dict
        assert len(bodega_dict['camiones']) == 1
        assert bodega_dict['camiones'][0]['placa'] == 'TEST999'
