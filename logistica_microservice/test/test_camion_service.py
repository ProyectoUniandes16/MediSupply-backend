import pytest
from src.services.camion_service import (
    crear_camion,
    listar_camiones,
    obtener_camion,
    listar_camiones_por_bodega,
    actualizar_estado_camion,
    CamionServiceError
)
from src.services.zona_service import crear_zona
from src.services.bodega_service import crear_bodega
from src.services.tipo_camion_service import crear_tipo_camion


def test_crear_camion_exito(app):
    """Test de creación exitosa de un camión"""
    with app.app_context():
        # Crear zona
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
        bodega = crear_bodega(bodega_data)
        
        # Crear tipo de camión
        tipo_data = {
            'nombre': 'Refrigerado',
            'descripcion': 'Camión refrigerado'
        }
        tipo = crear_tipo_camion(tipo_data)
        
        # Crear camión
        camion_data = {
            'placa': 'ABC123',
            'capacidad_kg': 5000.0,
            'capacidad_m3': 50.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        }
        
        result = crear_camion(camion_data)
        
        assert 'id' in result
        assert result['placa'] == 'ABC123'
        assert result['capacidad_kg'] == 5000.0
        assert result['estado'] == 'disponible'
        assert 'tipo_camion' in result


def test_crear_camion_sin_datos(app):
    """Test de creación de camión sin datos"""
    with app.app_context():
        with pytest.raises(CamionServiceError) as excinfo:
            crear_camion(None)
        
        assert excinfo.value.status_code == 400
        assert 'No se proporcionaron datos' in excinfo.value.message['error']


def test_crear_camion_campos_faltantes(app):
    """Test de creación de camión con campos faltantes"""
    with app.app_context():
        data = {
            'placa': 'XYZ789'
        }
        
        with pytest.raises(CamionServiceError) as excinfo:
            crear_camion(data)
        
        assert excinfo.value.status_code == 400
        assert 'Campos faltantes' in excinfo.value.message['error']


def test_crear_camion_bodega_inexistente(app):
    """Test de creación de camión con bodega inexistente"""
    with app.app_context():
        # Crear tipo de camión
        tipo_data = {
            'nombre': 'Sin Refrigeración'
        }
        tipo = crear_tipo_camion(tipo_data)
        
        data = {
            'placa': 'DEF456',
            'capacidad_kg': 3000.0,
            'capacidad_m3': 30.0,
            'bodega_id': 'id-inexistente',
            'tipo_camion_id': tipo['id']
        }
        
        with pytest.raises(CamionServiceError) as excinfo:
            crear_camion(data)
        
        assert excinfo.value.status_code == 404
        assert 'bodega especificada no existe' in excinfo.value.message['error']


def test_crear_camion_tipo_inexistente(app):
    """Test de creación de camión con tipo inexistente"""
    with app.app_context():
        # Crear zona y bodega
        zona_data = {
            'nombre': 'Zona Test 2',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        zona = crear_zona(zona_data)
        
        bodega_data = {
            'nombre': 'Bodega Test 2',
            'ubicacion': 'Ubicacion Test 2',
            'zona_id': zona['id']
        }
        bodega = crear_bodega(bodega_data)
        
        data = {
            'placa': 'GHI789',
            'capacidad_kg': 4000.0,
            'capacidad_m3': 40.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': 'id-inexistente'
        }
        
        with pytest.raises(CamionServiceError) as excinfo:
            crear_camion(data)
        
        assert excinfo.value.status_code == 404
        assert 'tipo de camión especificado no existe' in excinfo.value.message['error']


def test_crear_camion_placa_duplicada(app):
    """Test de creación de camión con placa duplicada"""
    with app.app_context():
        # Crear zona, bodega y tipo
        zona = crear_zona({
            'nombre': 'Zona Duplicada',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Duplicada',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({
            'nombre': 'Mixto'
        })
        
        # Crear primer camión
        camion_data = {
            'placa': 'JKL012',
            'capacidad_kg': 2000.0,
            'capacidad_m3': 20.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        }
        crear_camion(camion_data)
        
        # Intentar crear con placa duplicada
        with pytest.raises(CamionServiceError) as excinfo:
            crear_camion(camion_data)
        
        assert excinfo.value.status_code == 400
        assert 'Ya existe un camión con esa placa' in excinfo.value.message['error']


def test_crear_camion_capacidad_invalida(app):
    """Test de creación de camión con capacidad inválida"""
    with app.app_context():
        zona = crear_zona({
            'nombre': 'Zona Cap',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Cap',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({
            'nombre': 'Tipo Cap'
        })
        
        data = {
            'placa': 'MNO345',
            'capacidad_kg': -100.0,  # Capacidad negativa
            'capacidad_m3': 20.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        }
        
        with pytest.raises(CamionServiceError) as excinfo:
            crear_camion(data)
        
        assert excinfo.value.status_code == 400
        assert 'capacidades deben ser mayores a 0' in excinfo.value.message['error']


def test_listar_camiones(app):
    """Test de listado de camiones"""
    with app.app_context():
        result = listar_camiones()
        
        assert 'data' in result
        assert 'total' in result
        assert isinstance(result['data'], list)


def test_obtener_camion_existente(app):
    """Test de obtención de camión existente"""
    with app.app_context():
        # Crear datos necesarios
        zona = crear_zona({
            'nombre': 'Zona Obtener',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Obtener',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({
            'nombre': 'Tipo Obtener'
        })
        
        camion_data = {
            'placa': 'PQR678',
            'capacidad_kg': 3500.0,
            'capacidad_m3': 35.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        }
        
        camion_creado = crear_camion(camion_data)
        camion_obtenido = obtener_camion(camion_creado['id'])
        
        assert camion_obtenido['id'] == camion_creado['id']
        assert camion_obtenido['placa'] == 'PQR678'


def test_obtener_camion_no_existente(app):
    """Test de obtención de camión no existente"""
    with app.app_context():
        with pytest.raises(CamionServiceError) as excinfo:
            obtener_camion('id-inexistente')
        
        assert excinfo.value.status_code == 404


def test_listar_camiones_por_bodega(app):
    """Test de listado de camiones por bodega"""
    with app.app_context():
        # Crear datos necesarios
        zona = crear_zona({
            'nombre': 'Zona Lista',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Lista',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({
            'nombre': 'Tipo Lista'
        })
        
        # Crear dos camiones para la bodega
        crear_camion({
            'placa': 'STU901',
            'capacidad_kg': 2500.0,
            'capacidad_m3': 25.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        })
        
        crear_camion({
            'placa': 'VWX234',
            'capacidad_kg': 3000.0,
            'capacidad_m3': 30.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        })
        
        result = listar_camiones_por_bodega(bodega['id'])
        
        assert 'camiones' in result
        assert 'bodega_id' in result
        assert 'bodega_nombre' in result
        assert result['total'] == 2
        assert result['bodega_nombre'] == 'Bodega Lista'


def test_listar_camiones_bodega_inexistente(app):
    """Test de listado de camiones de bodega inexistente"""
    with app.app_context():
        with pytest.raises(CamionServiceError) as excinfo:
            listar_camiones_por_bodega('id-inexistente')
        
        assert excinfo.value.status_code == 404


def test_actualizar_estado_camion(app):
    """Test de actualización de estado de camión"""
    with app.app_context():
        # Crear datos necesarios
        zona = crear_zona({
            'nombre': 'Zona Estado',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        })
        
        bodega = crear_bodega({
            'nombre': 'Bodega Estado',
            'ubicacion': 'Ubicacion',
            'zona_id': zona['id']
        })
        
        tipo = crear_tipo_camion({
            'nombre': 'Tipo Estado'
        })
        
        camion = crear_camion({
            'placa': 'YZA567',
            'capacidad_kg': 4000.0,
            'capacidad_m3': 40.0,
            'bodega_id': bodega['id'],
            'tipo_camion_id': tipo['id']
        })
        
        # Actualizar estado
        camion_actualizado = actualizar_estado_camion(camion['id'], 'en_ruta')
        
        assert camion_actualizado['estado'] == 'en_ruta'


def test_actualizar_estado_camion_invalido(app):
    """Test de actualización con estado inválido"""
    with app.app_context():
        with pytest.raises(CamionServiceError) as excinfo:
            actualizar_estado_camion('cualquier-id', 'estado_invalido')
        
        assert excinfo.value.status_code == 400
        assert 'Estado inválido' in excinfo.value.message['error']
