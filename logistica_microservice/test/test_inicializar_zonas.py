"""
Pruebas para el servicio de inicialización de zonas
"""
import pytest
from src.models.zona import Zona
from src.models.bodega import Bodega
from src.models.camion import Camion
from src.models.tipo_camion import TipoCamion
from src.services.zona_service import inicializar_zonas, ZonaServiceError
from src.services.tipo_camion_service import inicializar_tipos_camion


def test_inicializar_zonas_exito(app):
    """
    Test: Inicializar zonas exitosamente
    """
    with app.app_context():
        # Primero inicializar tipos de camión
        inicializar_tipos_camion()
        
        # Ejecutar inicialización
        resultado = inicializar_zonas()
        
        # Verificar resultado
        assert 'mensaje' in resultado
        assert 'zonas_creadas' in resultado
        assert 'bodegas_creadas' in resultado
        assert 'camiones_creados' in resultado
        assert resultado['total_zonas'] == 4
        assert resultado['total_bodegas'] == 4
        assert resultado['total_camiones'] == 12  # 3 camiones por cada una de las 4 zonas
        
        # Verificar que las zonas se crearon
        zonas = Zona.query.all()
        assert len(zonas) == 4
        
        # Verificar nombres de zonas
        nombres_zonas = [z.nombre for z in zonas]
        assert "México - Ciudad de México" in nombres_zonas
        assert "Colombia - Bogotá" in nombres_zonas
        assert "Ecuador - Quito" in nombres_zonas
        assert "Perú - Lima" in nombres_zonas
        
        # Verificar bodegas
        bodegas = Bodega.query.all()
        assert len(bodegas) == 4
        
        # Verificar camiones
        camiones = Camion.query.all()
        assert len(camiones) == 12
        
        # Verificar que cada bodega tiene 3 camiones
        for bodega in bodegas:
            assert len(bodega.camiones) == 3
            
            # Verificar que hay un camión de cada tipo
            tipos = [c.tipo_camion.nombre for c in bodega.camiones]
            assert "Refrigerado" in tipos
            assert "Sin Refrigeración" in tipos
            assert "Mixto" in tipos


def test_inicializar_zonas_sin_tipos_camion(app):
    """
    Test: Intentar inicializar zonas sin tipos de camión
    """
    with app.app_context():
        # No inicializar tipos de camión
        
        # Debe lanzar error
        with pytest.raises(ZonaServiceError) as exc_info:
            inicializar_zonas()
        
        assert exc_info.value.status_code == 400
        assert 'TIPOS_CAMION_NO_INICIALIZADOS' in str(exc_info.value.message)


def test_inicializar_zonas_ya_existentes(app):
    """
    Test: Inicializar zonas que ya existen
    """
    with app.app_context():
        # Primero inicializar tipos de camión
        inicializar_tipos_camion()
        
        # Primera inicialización
        resultado1 = inicializar_zonas()
        assert resultado1['total_zonas'] == 4
        
        # Segunda inicialización (zonas ya existen)
        resultado2 = inicializar_zonas()
        assert 'mensaje' in resultado2
        assert 'zonas_existentes' in resultado2 or 'todas las zonas ya estaban' in resultado2['mensaje'].lower()
        
        # Verificar que no se duplicaron
        zonas = Zona.query.all()
        assert len(zonas) == 4


def test_inicializar_zonas_endpoint_exito(client, auth_headers):
    """
    Test: Endpoint de inicialización exitoso
    """
    # Primero inicializar tipos de camión
    response_tipos = client.post(
        '/tipo-camion/inicializar',
        headers=auth_headers
    )
    assert response_tipos.status_code == 201
    
    # Inicializar zonas
    response = client.post(
        '/zona/inicializar',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'mensaje' in data
    assert 'zonas_creadas' in data
    assert data['total_zonas'] == 4
    assert data['total_bodegas'] == 4
    assert data['total_camiones'] == 12


def test_inicializar_zonas_endpoint_sin_tipos_camion(client, auth_headers):
    """
    Test: Endpoint sin tipos de camión inicializados
    """
    response = client.post(
        '/zona/inicializar',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'TIPOS_CAMION_NO_INICIALIZADOS' in data['codigo']


def test_zonas_inicializadas_tienen_coordenadas_correctas(app):
    """
    Test: Verificar que las zonas tienen las coordenadas correctas
    """
    with app.app_context():
        # Inicializar tipos y zonas
        inicializar_tipos_camion()
        inicializar_zonas()
        
        # Verificar México - Ciudad de México
        mexico = Zona.query.filter_by(nombre="México - Ciudad de México").first()
        assert mexico is not None
        assert mexico.latitud_minima == 19.27
        assert mexico.latitud_maxima == 19.59
        assert mexico.longitud_minima == -99.29
        assert mexico.longitud_maxima == -98.97
        
        # Verificar Colombia - Bogotá
        bogota = Zona.query.filter_by(nombre="Colombia - Bogotá").first()
        assert bogota is not None
        assert bogota.latitud_minima == 4.6
        assert bogota.latitud_maxima == 4.73
        assert bogota.longitud_minima == -74.12
        assert bogota.longitud_maxima == -74.04
        
        # Verificar Ecuador - Quito
        quito = Zona.query.filter_by(nombre="Ecuador - Quito").first()
        assert quito is not None
        assert quito.latitud_minima == -0.3
        assert quito.latitud_maxima == 0.05
        
        # Verificar Perú - Lima
        lima = Zona.query.filter_by(nombre="Perú - Lima").first()
        assert lima is not None
        assert lima.latitud_minima == -12.2
        assert lima.latitud_maxima == -11.7


def test_bodegas_inicializadas_tienen_ubicacion_correcta(app):
    """
    Test: Verificar que las bodegas tienen ubicaciones válidas
    """
    with app.app_context():
        # Inicializar tipos y zonas
        inicializar_tipos_camion()
        inicializar_zonas()
        
        # Verificar Bodega Kennedy en Bogotá
        bodega_kennedy = Bodega.query.filter_by(nombre="Bodega Kennedy").first()
        assert bodega_kennedy is not None
        assert bodega_kennedy.ubicacion == "4.636767,-74.140675"
        
        # Verificar que todas las bodegas tienen formato de ubicación válido
        bodegas = Bodega.query.all()
        for bodega in bodegas:
            # La ubicación debe tener formato "latitud,longitud"
            partes = bodega.ubicacion.split(',')
            assert len(partes) == 2
            # Verificar que son números
            float(partes[0])  # Debe poder convertirse a float
            float(partes[1])  # Debe poder convertirse a float


def test_camiones_inicializados_tienen_datos_correctos(app):
    """
    Test: Verificar que los camiones tienen los datos correctos
    """
    with app.app_context():
        # Inicializar tipos y zonas
        inicializar_tipos_camion()
        inicializar_zonas()
        
        # Verificar camiones
        camiones = Camion.query.all()
        assert len(camiones) == 12
        
        # Verificar que todos tienen estado disponible
        for camion in camiones:
            assert camion.estado == "disponible"
            assert camion.capacidad_kg > 0
            assert camion.capacidad_m3 > 0
            assert camion.placa is not None
            assert camion.bodega_id is not None
            assert camion.tipo_camion_id is not None
        
        # Verificar placas únicas
        placas = [c.placa for c in camiones]
        assert len(placas) == len(set(placas))  # No hay placas duplicadas
        
        # Verificar que hay camiones de cada tipo
        tipos_camiones = [c.tipo_camion.nombre for c in camiones]
        assert tipos_camiones.count("Refrigerado") == 4
        assert tipos_camiones.count("Sin Refrigeración") == 4
        assert tipos_camiones.count("Mixto") == 4
