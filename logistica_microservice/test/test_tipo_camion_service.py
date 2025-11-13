import pytest
from src.services.tipo_camion_service import (
    crear_tipo_camion,
    listar_tipos_camion,
    obtener_tipo_camion,
    inicializar_tipos_camion,
    TipoCamionServiceError
)


def test_crear_tipo_camion_exito(app):
    """Test de creación exitosa de un tipo de camión"""
    with app.app_context():
        data = {
            'nombre': 'Refrigerado',
            'descripcion': 'Camión con refrigeración'
        }
        
        result = crear_tipo_camion(data)
        
        assert 'id' in result
        assert result['nombre'] == 'Refrigerado'
        assert result['descripcion'] == 'Camión con refrigeración'


def test_crear_tipo_camion_sin_datos(app):
    """Test de creación de tipo de camión sin datos"""
    with app.app_context():
        with pytest.raises(TipoCamionServiceError) as excinfo:
            crear_tipo_camion(None)
        
        assert excinfo.value.status_code == 400
        assert 'No se proporcionaron datos' in excinfo.value.message['error']


def test_crear_tipo_camion_sin_nombre(app):
    """Test de creación de tipo de camión sin nombre"""
    with app.app_context():
        data = {
            'descripcion': 'Test'
        }
        
        with pytest.raises(TipoCamionServiceError) as excinfo:
            crear_tipo_camion(data)
        
        assert excinfo.value.status_code == 400
        assert 'nombre es requerido' in excinfo.value.message['error']


def test_crear_tipo_camion_duplicado(app):
    """Test de creación de tipo de camión con nombre duplicado"""
    with app.app_context():
        data = {
            'nombre': 'Mixto',
            'descripcion': 'Camión mixto'
        }
        
        crear_tipo_camion(data)
        
        with pytest.raises(TipoCamionServiceError) as excinfo:
            crear_tipo_camion(data)
        
        assert excinfo.value.status_code == 400
        assert 'Ya existe un tipo de camión con ese nombre' in excinfo.value.message['error']


def test_listar_tipos_camion(app):
    """Test de listado de tipos de camión"""
    with app.app_context():
        data1 = {
            'nombre': 'Tipo 1',
            'descripcion': 'Descripción 1'
        }
        data2 = {
            'nombre': 'Tipo 2',
            'descripcion': 'Descripción 2'
        }
        
        crear_tipo_camion(data1)
        crear_tipo_camion(data2)
        
        result = listar_tipos_camion()
        
        assert 'data' in result
        assert result['total'] >= 2


def test_obtener_tipo_camion_existente(app):
    """Test de obtención de tipo de camión existente"""
    with app.app_context():
        data = {
            'nombre': 'Sin Refrigeración',
            'descripcion': 'Camión estándar'
        }
        
        tipo_creado = crear_tipo_camion(data)
        tipo_obtenido = obtener_tipo_camion(tipo_creado['id'])
        
        assert tipo_obtenido['id'] == tipo_creado['id']
        assert tipo_obtenido['nombre'] == 'Sin Refrigeración'


def test_obtener_tipo_camion_no_existente(app):
    """Test de obtención de tipo de camión no existente"""
    with app.app_context():
        with pytest.raises(TipoCamionServiceError) as excinfo:
            obtener_tipo_camion('id-inexistente')
        
        assert excinfo.value.status_code == 404


def test_inicializar_tipos_camion(app):
    """Test de inicialización de tipos de camión predeterminados"""
    with app.app_context():
        result = inicializar_tipos_camion()
        
        assert 'message' in result
        assert 'tipos_creados' in result
        assert 'total' in result
        
        # Verificar que los tipos fueron creados
        tipos = listar_tipos_camion()
        nombres = [tipo['nombre'] for tipo in tipos['data']]
        
        assert 'Refrigerado' in nombres
        assert 'Sin Refrigeración' in nombres
        assert 'Mixto' in nombres


def test_inicializar_tipos_camion_ya_existentes(app):
    """Test de inicialización cuando los tipos ya existen"""
    with app.app_context():
        # Primera inicialización
        inicializar_tipos_camion()
        
        # Segunda inicialización (no debe crear duplicados)
        result = inicializar_tipos_camion()
        
        assert result['total'] == 0
