import pytest
from src.services.zona_service import crear_zona, listar_zonas, obtener_zona, listar_zonas_con_bodegas, ZonaServiceError
from src.models.zona import Zona


def test_crear_zona_exito(app):
    """Test de creación exitosa de una zona"""
    with app.app_context():
        data = {
            'nombre': 'Zona Norte',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        
        result = crear_zona(data)
        
        assert 'id' in result
        assert result['nombre'] == 'Zona Norte'
        assert result['latitud_maxima'] == 10.0


def test_crear_zona_sin_datos(app):
    """Test de creación de zona sin datos"""
    with app.app_context():
        with pytest.raises(ZonaServiceError) as excinfo:
            crear_zona(None)
        
        assert excinfo.value.status_code == 400
        assert 'No se proporcionaron datos' in excinfo.value.message['error']


def test_crear_zona_campos_faltantes(app):
    """Test de creación de zona con campos faltantes"""
    with app.app_context():
        data = {
            'nombre': 'Zona Sur'
        }
        
        with pytest.raises(ZonaServiceError) as excinfo:
            crear_zona(data)
        
        assert excinfo.value.status_code == 400
        assert 'Campos faltantes' in excinfo.value.message['error']


def test_crear_zona_coordenadas_invalidas(app):
    """Test de creación de zona con coordenadas inválidas"""
    with app.app_context():
        data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 95.0,  # Fuera de rango
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        
        with pytest.raises(ZonaServiceError) as excinfo:
            crear_zona(data)
        
        assert excinfo.value.status_code == 400


def test_crear_zona_duplicada(app):
    """Test de creación de zona con nombre duplicado"""
    with app.app_context():
        data = {
            'nombre': 'Zona Centro',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        
        crear_zona(data)
        
        with pytest.raises(ZonaServiceError) as excinfo:
            crear_zona(data)
        
        assert excinfo.value.status_code == 400
        assert 'Ya existe una zona con ese nombre' in excinfo.value.message['error']


def test_listar_zonas(app):
    """Test de listado de zonas"""
    with app.app_context():
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
        
        crear_zona(data1)
        crear_zona(data2)
        
        result = listar_zonas()
        
        assert 'data' in result
        assert result['total'] == 2
        assert len(result['data']) == 2


def test_obtener_zona_existente(app):
    """Test de obtención de zona existente"""
    with app.app_context():
        data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        
        zona_creada = crear_zona(data)
        zona_obtenida = obtener_zona(zona_creada['id'])
        
        assert zona_obtenida['id'] == zona_creada['id']
        assert zona_obtenida['nombre'] == 'Zona Test'


def test_obtener_zona_no_existente(app):
    """Test de obtención de zona no existente"""
    with app.app_context():
        with pytest.raises(ZonaServiceError) as excinfo:
            obtener_zona('id-inexistente')
        
        assert excinfo.value.status_code == 404


def test_zona_to_dict_with_bodegas(app):
    """Test del método to_dict_with_bodegas de Zona"""
    from src.models.bodega import Bodega
    from src import db
    
    with app.app_context():
        # Crear una zona
        data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona_creada = crear_zona(data)
        
        # Obtener la zona del DB
        zona_db = Zona.query.filter_by(id=zona_creada['id']).first()
        
        # Crear una bodega asociada
        bodega = Bodega(
            nombre='Bodega Test',
            ubicacion='Ubicacion Test'
        )
        bodega.zonas.append(zona_db)
        db.session.add(bodega)
        db.session.commit()
        
        # Probar serialización con bodegas
        zona_dict = zona_db.to_dict_with_bodegas()
        
        assert 'id' in zona_dict
        assert zona_dict['nombre'] == 'Zona Test'
        assert 'bodegas' in zona_dict
        assert len(zona_dict['bodegas']) == 1
        assert zona_dict['bodegas'][0]['nombre'] == 'Bodega Test'


def test_listar_zonas_con_bodegas_vacio(app):
    """Test de listar zonas con bodegas cuando no hay zonas"""
    with app.app_context():
        result = listar_zonas_con_bodegas()
        
        assert 'data' in result
        assert result['total'] == 0
        assert len(result['data']) == 0


def test_listar_zonas_con_bodegas_exitoso(app):
    """Test de listar zonas con sus bodegas"""
    from src.models.bodega import Bodega
    from src import db
    
    with app.app_context():
        # Crear zonas
        zona1_data = {
            'nombre': 'Zona 1',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona2_data = {
            'nombre': 'Zona 2',
            'latitud_maxima': 15.0,
            'latitud_minima': 10.0,
            'longitud_maxima': -65.0,
            'longitud_minima': -70.0
        }
        zona1 = crear_zona(zona1_data)
        zona2 = crear_zona(zona2_data)
        
        # Obtener zonas del DB
        zona1_db = Zona.query.filter_by(id=zona1['id']).first()
        zona2_db = Zona.query.filter_by(id=zona2['id']).first()
        
        # Crear bodegas
        bodega1 = Bodega(nombre='Bodega 1', ubicacion='Ubicacion 1')
        bodega1.zonas.append(zona1_db)
        bodega2 = Bodega(nombre='Bodega 2', ubicacion='Ubicacion 2')
        bodega2.zonas.append(zona2_db)
        db.session.add(bodega1)
        db.session.add(bodega2)
        db.session.commit()
        
        # Listar zonas con bodegas
        result = listar_zonas_con_bodegas()
        
        assert 'data' in result
        assert result['total'] == 2
        assert 'bodegas' in result['data'][0]
        assert len(result['data'][0]['bodegas']) == 1
