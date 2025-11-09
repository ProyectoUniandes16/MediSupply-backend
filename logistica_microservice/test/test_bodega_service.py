import pytest
from src.services.bodega_service import crear_bodega, listar_bodegas, obtener_bodega, BodegaServiceError
from src.services.zona_service import crear_zona
from src.models.bodega import Bodega


def test_crear_bodega_exito(app):
    """Test de creación exitosa de una bodega"""
    with app.app_context():
        # Crear una zona primero
        zona_data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona = crear_zona(zona_data)
        
        bodega_data = {
            'nombre': 'Bodega Principal',
            'ubicacion': 'Calle 123 #45-67',
            'zona_id': zona['id']
        }
        
        result = crear_bodega(bodega_data)
        
        assert 'id' in result
        assert result['nombre'] == 'Bodega Principal'
        assert result['ubicacion'] == 'Calle 123 #45-67'


def test_crear_bodega_sin_datos(app):
    """Test de creación de bodega sin datos"""
    with app.app_context():
        with pytest.raises(BodegaServiceError) as excinfo:
            crear_bodega(None)
        
        assert excinfo.value.status_code == 400
        assert 'No se proporcionaron datos' in excinfo.value.message['error']


def test_crear_bodega_campos_faltantes(app):
    """Test de creación de bodega con campos faltantes"""
    with app.app_context():
        data = {
            'nombre': 'Bodega Test'
        }
        
        with pytest.raises(BodegaServiceError) as excinfo:
            crear_bodega(data)
        
        assert excinfo.value.status_code == 400
        assert 'Campos faltantes' in excinfo.value.message['error']


def test_crear_bodega_zona_inexistente(app):
    """Test de creación de bodega con zona inexistente"""
    with app.app_context():
        data = {
            'nombre': 'Bodega Test',
            'ubicacion': 'Calle 1',
            'zona_id': 'id-inexistente'
        }
        
        with pytest.raises(BodegaServiceError) as excinfo:
            crear_bodega(data)
        
        assert excinfo.value.status_code == 404
        assert 'La zona especificada no existe' in excinfo.value.message['error']


def test_listar_bodegas(app):
    """Test de listado de bodegas"""
    with app.app_context():
        # Crear una zona
        zona_data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona = crear_zona(zona_data)
        
        # Crear bodegas
        bodega1 = {
            'nombre': 'Bodega 1',
            'ubicacion': 'Ubicacion 1',
            'zona_id': zona['id']
        }
        bodega2 = {
            'nombre': 'Bodega 2',
            'ubicacion': 'Ubicacion 2',
            'zona_id': zona['id']
        }
        
        crear_bodega(bodega1)
        crear_bodega(bodega2)
        
        result = listar_bodegas()
        
        assert 'data' in result
        assert result['total'] == 2
        assert len(result['data']) == 2


def test_obtener_bodega_existente(app):
    """Test de obtención de bodega existente"""
    with app.app_context():
        # Crear una zona
        zona_data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona = crear_zona(zona_data)
        
        # Crear bodega
        bodega_data = {
            'nombre': 'Bodega Test',
            'ubicacion': 'Ubicacion Test',
            'zona_id': zona['id']
        }
        
        bodega_creada = crear_bodega(bodega_data)
        bodega_obtenida = obtener_bodega(bodega_creada['id'])
        
        assert bodega_obtenida['id'] == bodega_creada['id']
        assert bodega_obtenida['nombre'] == 'Bodega Test'


def test_obtener_bodega_no_existente(app):
    """Test de obtención de bodega no existente"""
    with app.app_context():
        with pytest.raises(BodegaServiceError) as excinfo:
            obtener_bodega('id-inexistente')
        
        assert excinfo.value.status_code == 404


def test_bodega_to_dict_with_zonas(app):
    """Test del método to_dict_with_zonas de Bodega"""
    from src import db
    
    with app.app_context():
        # Crear una zona
        zona_data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona = crear_zona(zona_data)
        
        # Crear una bodega asociada
        bodega_data = {
            'nombre': 'Bodega Test',
            'ubicacion': 'Ubicacion Test',
            'zona_id': zona['id']
        }
        bodega_creada = crear_bodega(bodega_data)
        
        # Obtener bodega del DB
        bodega_db = Bodega.query.filter_by(id=bodega_creada['id']).first()
        
        # Probar serialización con zonas
        bodega_dict = bodega_db.to_dict_with_zonas()
        
        assert 'id' in bodega_dict
        assert bodega_dict['nombre'] == 'Bodega Test'
        assert 'zonas' in bodega_dict
        assert len(bodega_dict['zonas']) == 1
        assert bodega_dict['zonas'][0]['nombre'] == 'Zona Test'
