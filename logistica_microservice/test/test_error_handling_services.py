import pytest
from src.services.camion_service import CamionServiceError
from src.services.tipo_camion_service import TipoCamionServiceError
from unittest.mock import patch
from src import db


def test_crear_camion_db_error(app):
    """Test de error de base de datos al crear camión"""
    from src.services.camion_service import crear_camion
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    
    with app.app_context():
        zona = crear_zona({
            'nombre': 'Zona DB Error',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega DB Error',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({'nombre': 'Tipo DB Error'})
        
        with patch('src.services.camion_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('Database error')
            
            data = {
                'placa': 'ERROR123',
                'capacidad_kg': 1000.0,
                'capacidad_m3': 10.0,
                'bodega_id': bodega['id'],
                'tipo_camion_id': tipo['id']
            }
            
            with pytest.raises(CamionServiceError) as excinfo:
                crear_camion(data)
            
            assert excinfo.value.status_code == 500


def test_listar_camiones_db_error(app):
    """Test de error de base de datos al listar camiones"""
    from src.services.camion_service import listar_camiones
    from src.models.camion import Camion
    
    with app.app_context():
        with patch.object(Camion, 'query') as mock_query:
            mock_query.all.side_effect = Exception('Database error')
            
            with pytest.raises(CamionServiceError) as excinfo:
                listar_camiones()
            
            assert excinfo.value.status_code == 500


def test_obtener_camion_db_error(app):
    """Test de error de base de datos al obtener camión"""
    from src.services.camion_service import obtener_camion, crear_camion
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    
    with app.app_context():
        # Primero crear un camión válido
        zona = crear_zona({
            'nombre': 'Zona Get Error',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Get Error',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({'nombre': 'Tipo Get Error'})
        
        camion = crear_camion({
            'placa': 'GETERR123',
            'capacidad_kg': 1000.0,
            'capacidad_m3': 10.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        })
        
        # Simular error de DB después de encontrar el camión
        with patch('src.services.camion_service.Camion') as mock_camion:
            mock_camion.query.get.return_value.to_dict_with_tipo.side_effect = Exception('Database error')
            
            with pytest.raises(CamionServiceError) as excinfo:
                obtener_camion(camion['id'])
            
            assert excinfo.value.status_code == 500


def test_listar_camiones_por_bodega_db_error(app):
    """Test de error al listar camiones por bodega"""
    from src.services.camion_service import listar_camiones_por_bodega
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    
    with app.app_context():
        zona = crear_zona({
            'nombre': 'Zona Lista Error',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Lista Error',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        with patch('src.services.camion_service.Camion.query') as mock_query:
            mock_query.filter_by.side_effect = Exception('Database error')
            
            with pytest.raises(CamionServiceError) as excinfo:
                listar_camiones_por_bodega(bodega['id'])
            
            assert excinfo.value.status_code == 500


def test_actualizar_estado_camion_db_error(app):
    """Test de error al actualizar estado de camión"""
    from src.services.camion_service import actualizar_estado_camion, crear_camion
    from src.services.zona_service import crear_zona
    from src.services.bodega_service import crear_bodega
    from src.services.tipo_camion_service import crear_tipo_camion
    
    with app.app_context():
        zona = crear_zona({
            'nombre': 'Zona Update Error',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Update Error',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({'nombre': 'Tipo Update Error'})
        
        camion = crear_camion({
            'placa': 'UPD123',
            'capacidad_kg': 1000.0,
            'capacidad_m3': 10.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        })
        
        with patch('src.services.camion_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('Database error')
            
            with pytest.raises(CamionServiceError) as excinfo:
                actualizar_estado_camion(camion['id'], 'en_ruta')
            
            assert excinfo.value.status_code == 500


def test_crear_tipo_camion_db_error(app):
    """Test de error de base de datos al crear tipo"""
    from src.services.tipo_camion_service import crear_tipo_camion
    
    with app.app_context():
        with patch('src.services.tipo_camion_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('Database error')
            
            data = {'nombre': 'Tipo Error DB'}
            
            with pytest.raises(TipoCamionServiceError) as excinfo:
                crear_tipo_camion(data)
            
            assert excinfo.value.status_code == 500


def test_listar_tipos_camion_db_error(app):
    """Test de error al listar tipos de camión"""
    from src.services.tipo_camion_service import listar_tipos_camion
    from src.models.tipo_camion import TipoCamion
    
    with app.app_context():
        with patch.object(TipoCamion, 'query') as mock_query:
            mock_query.all.side_effect = Exception('Database error')
            
            with pytest.raises(TipoCamionServiceError) as excinfo:
                listar_tipos_camion()
            
            assert excinfo.value.status_code == 500


def test_obtener_tipo_camion_db_error(app):
    """Test de error al obtener tipo de camión"""
    from src.services.tipo_camion_service import obtener_tipo_camion, crear_tipo_camion
    
    with app.app_context():
        # Primero crear un tipo válido
        tipo = crear_tipo_camion({'nombre': 'Tipo Get Error'})
        
        # Simular error de DB después de encontrar el tipo
        with patch('src.services.tipo_camion_service.TipoCamion') as mock_tipo:
            mock_tipo.query.get.return_value.to_dict.side_effect = Exception('Database error')
            
            with pytest.raises(TipoCamionServiceError) as excinfo:
                obtener_tipo_camion(tipo['id'])
            
            assert excinfo.value.status_code == 500


def test_inicializar_tipos_camion_db_error(app):
    """Test de error al inicializar tipos de camión"""
    from src.services.tipo_camion_service import inicializar_tipos_camion
    
    with app.app_context():
        with patch('src.services.tipo_camion_service.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('Database error')
            
            with pytest.raises(TipoCamionServiceError) as excinfo:
                inicializar_tipos_camion()
            
            assert excinfo.value.status_code == 500
