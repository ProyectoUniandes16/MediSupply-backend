import pytest
from unittest.mock import patch
from src import create_app
from flask_jwt_extended import create_access_token
from src.services.logistica import LogisticaServiceError


class TestListarZonasBlueprint:
    """Pruebas para el endpoint GET /zonas"""

    def test_consultar_zonas_success(self):
        """Prueba exitosa de consulta de zonas"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zonas_esperadas = {
            'zonas': [
                {'id': '123', 'nombre': 'México-CDMX', 'pais': 'México'},
                {'id': '456', 'nombre': 'Colombia-Bogotá', 'pais': 'Colombia'}
            ]
        }

        with patch('src.blueprints.logistica.listar_zonas', return_value=zonas_esperadas) as mock_listar:
            resp = client.get('/zona', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.get_json() == zonas_esperadas
        assert len(resp.get_json()['zonas']) == 2
        mock_listar.assert_called_once()

    def test_consultar_zonas_sin_token(self):
        """Prueba que el endpoint requiere autenticación"""
        app = create_app()
        client = app.test_client()

        resp = client.get('/zona')

        assert resp.status_code == 401

    def test_consultar_zonas_token_invalido(self):
        """Prueba con token inválido"""
        app = create_app()
        client = app.test_client()

        resp = client.get('/zona', headers={'Authorization': 'Bearer token-invalido'})

        assert resp.status_code == 422

    def test_consultar_zonas_lista_vacia(self):
        """Prueba cuando no hay zonas registradas"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        with patch('src.blueprints.logistica.listar_zonas', return_value={'zonas': []}):
            resp = client.get('/zona', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.get_json() == {'zonas': []}

    def test_consultar_zonas_service_error(self):
        """Prueba cuando el servicio de logística retorna error"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        with patch('src.blueprints.logistica.listar_zonas', 
                   side_effect=LogisticaServiceError('Error en servicio de logística', 500)):
            resp = client.get('/zona', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()
        assert 'Error en servicio de logística' in resp.get_json()['error']

    def test_consultar_zonas_unexpected_error(self):
        """Prueba cuando ocurre un error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        with patch('src.blueprints.logistica.listar_zonas', side_effect=Exception('Error inesperado')):
            resp = client.get('/zona', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()


class TestListarZonasConBodegasBlueprint:
    """Pruebas para el endpoint GET /zona-con-bodegas"""

    def test_consultar_zonas_con_bodegas_success(self):
        """Prueba exitosa de consulta de zonas con bodegas"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zonas_esperadas = {
            'data': [
                {
                    'id': '770e8400-e29b-41d4-a716-446655440001',
                    'nombre': 'Bogotá Centro',
                    'bodegas': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'nombre': 'Bodega Central',
                            'ubicacion': 'Av. Caracas #45-67'
                        }
                    ]
                }
            ],
            'total': 1
        }

        with patch('src.blueprints.logistica.listar_zonas_con_bodegas', return_value=zonas_esperadas) as mock_listar:
            resp = client.get('/zona-con-bodegas', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.get_json() == zonas_esperadas
        assert len(resp.get_json()['data']) == 1
        assert len(resp.get_json()['data'][0]['bodegas']) == 1
        mock_listar.assert_called_once()

    def test_consultar_zonas_con_bodegas_sin_token(self):
        """Prueba que el endpoint requiere autenticación"""
        app = create_app()
        client = app.test_client()

        resp = client.get('/zona-con-bodegas')

        assert resp.status_code == 401

    def test_consultar_zonas_con_bodegas_token_invalido(self):
        """Prueba con token inválido"""
        app = create_app()
        client = app.test_client()

        resp = client.get('/zona-con-bodegas', headers={'Authorization': 'Bearer token-invalido'})

        assert resp.status_code == 422

    def test_consultar_zonas_con_bodegas_lista_vacia(self):
        """Prueba cuando no hay zonas registradas"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        with patch('src.blueprints.logistica.listar_zonas_con_bodegas', return_value={'data': [], 'total': 0}):
            resp = client.get('/zona-con-bodegas', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.get_json() == {'data': [], 'total': 0}

    def test_consultar_zonas_con_bodegas_service_error(self):
        """Prueba cuando el servicio de logística retorna error"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        with patch('src.blueprints.logistica.listar_zonas_con_bodegas', 
                   side_effect=LogisticaServiceError('Error en servicio de logística', 500)):
            resp = client.get('/zona-con-bodegas', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_consultar_zonas_con_bodegas_unexpected_error(self):
        """Prueba cuando ocurre un error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        with patch('src.blueprints.logistica.listar_zonas_con_bodegas', side_effect=Exception('Error inesperado')):
            resp = client.get('/zona-con-bodegas', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_consultar_zonas_con_bodegas_multiple_zones(self):
        """Prueba con múltiples zonas y bodegas"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zonas_esperadas = {
            'data': [
                {
                    'id': 'zona-1',
                    'nombre': 'Zona 1',
                    'bodegas': [
                        {'id': 'bod-1', 'nombre': 'Bodega 1'},
                        {'id': 'bod-2', 'nombre': 'Bodega 2'}
                    ]
                },
                {
                    'id': 'zona-2',
                    'nombre': 'Zona 2',
                    'bodegas': [
                        {'id': 'bod-3', 'nombre': 'Bodega 3'}
                    ]
                }
            ],
            'total': 2
        }

        with patch('src.blueprints.logistica.listar_zonas_con_bodegas', return_value=zonas_esperadas):
            resp = client.get('/zona-con-bodegas', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['data']) == 2
        assert len(data['data'][0]['bodegas']) == 2
        assert len(data['data'][1]['bodegas']) == 1


class TestObtenerZonaDetalladaBlueprint:
    """Pruebas para el endpoint GET /zonas/<zona_id>/detalle"""

    def test_obtener_zona_detallada_success(self):
        """Prueba exitosa de obtención de zona detallada"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = 'zona-123'
        zona_detallada = {
            'id': zona_id,
            'nombre': 'México-CDMX',
            'pais': 'México',
            'bodegas': [
                {
                    'id': 'bodega-1',
                    'nombre': 'Bodega Central CDMX',
                    'latitud': 19.4326,
                    'longitud': -99.1332
                }
            ],
            'camiones': [
                {
                    'id': 'camion-1',
                    'placa': 'ABC-123',
                    'tipo': 'Refrigerado',
                    'disponible': True
                },
                {
                    'id': 'camion-2',
                    'placa': 'DEF-456',
                    'tipo': 'Sin Refrigeración',
                    'disponible': True
                }
            ]
        }

        with patch('src.blueprints.logistica.obtener_zona_detallada', 
                   return_value=zona_detallada) as mock_detalle:
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == zona_id
        assert len(data['bodegas']) == 1
        assert len(data['camiones']) == 2
        mock_detalle.assert_called_once_with(zona_id)

    def test_obtener_zona_detallada_sin_token(self):
        """Prueba que el endpoint requiere autenticación"""
        app = create_app()
        client = app.test_client()

        resp = client.get('/zona/zona-123/detalle')

        assert resp.status_code == 401

    def test_obtener_zona_detallada_token_invalido(self):
        """Prueba con token inválido"""
        app = create_app()
        client = app.test_client()

        resp = client.get('/zona/zona-123/detalle', headers={'Authorization': 'Bearer token-invalido'})

        assert resp.status_code == 422

    def test_obtener_zona_detallada_not_found(self):
        """Prueba cuando la zona no existe"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = 'zona-inexistente'
        with patch('src.blueprints.logistica.obtener_zona_detallada', 
                   side_effect=LogisticaServiceError('Zona no encontrada', 404)):
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 404
        assert 'error' in resp.get_json()
        assert 'Zona no encontrada' in resp.get_json()['error']

    def test_obtener_zona_detallada_sin_bodegas(self):
        """Prueba zona sin bodegas asociadas"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = 'zona-123'
        zona_detallada = {
            'id': zona_id,
            'nombre': 'Test Zone',
            'pais': 'Test',
            'bodegas': [],
            'camiones': []
        }

        with patch('src.blueprints.logistica.obtener_zona_detallada', return_value=zona_detallada):
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['bodegas'] == []
        assert data['camiones'] == []

    def test_obtener_zona_detallada_service_error(self):
        """Prueba cuando el servicio de logística retorna error"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = 'zona-123'
        with patch('src.blueprints.logistica.obtener_zona_detallada', 
                   side_effect=LogisticaServiceError('Error en servicio de logística', 500)):
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_obtener_zona_detallada_unexpected_error(self):
        """Prueba cuando ocurre un error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = 'zona-123'
        with patch('src.blueprints.logistica.obtener_zona_detallada', 
                   side_effect=Exception('Error inesperado')):
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_obtener_zona_detallada_con_uuid(self):
        """Prueba con un UUID válido"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = '550e8400-e29b-41d4-a716-446655440000'
        zona_detallada = {
            'id': zona_id,
            'nombre': 'Test Zone',
            'pais': 'Test',
            'bodegas': [],
            'camiones': []
        }

        with patch('src.blueprints.logistica.obtener_zona_detallada', return_value=zona_detallada):
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.get_json()['id'] == zona_id

    def test_obtener_zona_detallada_multiples_camiones(self):
        """Prueba zona con múltiples camiones de diferentes tipos"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        zona_id = 'zona-123'
        zona_detallada = {
            'id': zona_id,
            'nombre': 'Test',
            'pais': 'Test',
            'bodegas': [{'id': 'b1', 'nombre': 'Bodega 1'}],
            'camiones': [
                {'id': 'c1', 'placa': 'AAA-111', 'tipo': 'Refrigerado', 'disponible': True},
                {'id': 'c2', 'placa': 'BBB-222', 'tipo': 'Sin Refrigeración', 'disponible': True},
                {'id': 'c3', 'placa': 'CCC-333', 'tipo': 'Mixto', 'disponible': False}
            ]
        }

        with patch('src.blueprints.logistica.obtener_zona_detallada', return_value=zona_detallada):
            resp = client.get(f'/zona/{zona_id}/detalle', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['camiones']) == 3
        assert data['camiones'][0]['tipo'] == 'Refrigerado'
        assert data['camiones'][1]['tipo'] == 'Sin Refrigeración'
        assert data['camiones'][2]['tipo'] == 'Mixto'


class TestCrearRutaBlueprint:
    """Pruebas para el endpoint POST /rutas"""

    def test_crear_ruta_success(self):
        """Prueba exitosa de creación de ruta"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [
                {'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'pedido-001'},
                {'ubicacion': [-74.0445, 4.6760], 'pedido_id': 'pedido-002'}
            ]
        }

        ruta_creada = {
            'id': '880e8400-e29b-41d4-a716-446655440003',
            'bodega_id': datos_ruta['bodega_id'],
            'camion_id': datos_ruta['camion_id'],
            'zona_id': datos_ruta['zona_id'],
            'estado': 'pendiente',
            'fecha_creacion': '2025-11-13T10:30:00',
            'detalles': [
                {'id': '1', 'orden': 1, 'pedido_id': 'pedido-001'},
                {'id': '2', 'orden': 2, 'pedido_id': 'pedido-002'}
            ]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', 
                   return_value=ruta_creada) as mock_crear:
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['estado'] == 'pendiente'
        assert len(data['detalles']) == 2
        mock_crear.assert_called_once_with(datos_ruta)

    def test_crear_ruta_sin_token(self):
        """Prueba que el endpoint requiere autenticación"""
        app = create_app()
        client = app.test_client()

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        resp = client.post('/rutas', json=datos_ruta)

        assert resp.status_code == 401

    def test_crear_ruta_token_invalido(self):
        """Prueba con token inválido"""
        app = create_app()
        client = app.test_client()

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        resp = client.post('/rutas', 
                          json=datos_ruta,
                          headers={'Authorization': 'Bearer token-invalido'})

        assert resp.status_code == 422

    def test_crear_ruta_sin_datos(self):
        """Prueba sin enviar datos en el body"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        resp = client.post('/rutas', headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'error' in resp.get_json()
        assert 'Content-Type' in resp.get_json()['error']

    def test_crear_ruta_bodega_no_encontrada(self):
        """Prueba cuando la bodega no existe"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': 'bodega-inexistente',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', 
                   side_effect=LogisticaServiceError('Bodega no encontrada', 404)):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 404
        assert 'error' in resp.get_json()

    def test_crear_ruta_camion_no_disponible(self):
        """Prueba cuando el camión no está disponible"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', 
                   side_effect=LogisticaServiceError('El camión no está disponible', 400)):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_crear_ruta_estado_invalido(self):
        """Prueba con estado inválido"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'estado_invalido',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', 
                   side_effect=LogisticaServiceError('Estado inválido', 400)):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400

    def test_crear_ruta_service_error(self):
        """Prueba cuando el servicio de logística retorna error"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', 
                   side_effect=LogisticaServiceError('Error en servicio de logística', 500)):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_crear_ruta_unexpected_error(self):
        """Prueba cuando ocurre un error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', 
                   side_effect=Exception('Error inesperado')):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_crear_ruta_multiples_puntos(self):
        """Prueba creación de ruta con múltiples puntos"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [
                {'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'},
                {'ubicacion': [-74.0445, 4.6760], 'pedido_id': 'p2'},
                {'ubicacion': [-74.0817, 4.6097], 'pedido_id': 'p3'},
                {'ubicacion': [-74.1000, 4.6500], 'pedido_id': 'p4'},
                {'ubicacion': [-74.0500, 4.7000], 'pedido_id': 'p5'}
            ]
        }

        ruta_creada = {
            'id': '880e8400-e29b-41d4-a716-446655440003',
            'estado': 'pendiente',
            'detalles': [
                {'orden': i+1, 'pedido_id': f'p{i+1}'} 
                for i in range(5)
            ]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', return_value=ruta_creada):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 201
        assert len(resp.get_json()['detalles']) == 5

    def test_crear_ruta_estado_iniciado(self):
        """Prueba creación de ruta con estado iniciado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'iniciado',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }

        ruta_creada = {
            'id': '880e8400-e29b-41d4-a716-446655440003',
            'estado': 'iniciado',
            'fecha_inicio': '2025-11-13T10:30:00',
            'detalles': [{'orden': 1, 'pedido_id': 'p1'}]
        }

        with patch('src.blueprints.logistica.crear_ruta_entrega', return_value=ruta_creada):
            resp = client.post('/rutas', 
                             json=datos_ruta,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['estado'] == 'iniciado'
        assert 'fecha_inicio' in data


class TestOptimizarRutaBlueprint:
    """Pruebas para el endpoint POST /ruta-optima"""

    def test_optimizar_ruta_success_json(self):
        """Prueba exitosa de optimización de ruta en formato JSON"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [
                [-74.0445, 4.6760],
                [-74.0817, 4.6097],
                [-74.1000, 4.6500]
            ]
        }

        ruta_optima = {
            'ruta_optima': [
                [-74.0721, 4.7110],
                [-74.0445, 4.6760],
                [-74.0817, 4.6097],
                [-74.1000, 4.6500]
            ],
            'distancia_total': 15.5,
            'tiempo_estimado': 45
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   return_value=ruta_optima) as mock_optimizar:
            resp = client.post('/ruta-optima?formato=json', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.content_type == 'application/json'
        data = resp.get_json()
        assert data == ruta_optima
        assert len(data['ruta_optima']) == 4
        mock_optimizar.assert_called_once_with(payload, formato='json')

    def test_optimizar_ruta_success_html(self):
        """Prueba exitosa de optimización de ruta en formato HTML"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [
                [-74.0445, 4.6760],
                [-74.0817, 4.6097]
            ]
        }

        html_content = '<html><body><h1>Mapa de Ruta Optimizada</h1></body></html>'

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   return_value=html_content) as mock_optimizar:
            resp = client.post('/ruta-optima?formato=html', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.content_type == 'text/html; charset=utf-8'
        assert resp.get_data(as_text=True) == html_content
        mock_optimizar.assert_called_once_with(payload, formato='html')

    def test_optimizar_ruta_default_formato(self):
        """Prueba que el formato por defecto es JSON"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        ruta_optima = {'ruta_optima': []}

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   return_value=ruta_optima) as mock_optimizar:
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        assert resp.content_type == 'application/json'
        mock_optimizar.assert_called_once_with(payload, formato='json')

    def test_optimizar_ruta_sin_token(self):
        """Prueba que el endpoint requiere autenticación"""
        app = create_app()
        client = app.test_client()

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        resp = client.post('/ruta-optima', json=payload)

        assert resp.status_code == 401

    def test_optimizar_ruta_token_invalido(self):
        """Prueba con token inválido"""
        app = create_app()
        client = app.test_client()

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        resp = client.post('/ruta-optima', 
                          json=payload,
                          headers={'Authorization': 'Bearer token-invalido'})

        assert resp.status_code == 422

    def test_optimizar_ruta_sin_datos(self):
        """Prueba sin enviar datos en el body"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        # Enviar POST sin body - debería ser detectado como JSON vacío
        resp = client.post('/ruta-optima', 
                          json={},  # JSON vacío
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'codigo' in data
        assert data['codigo'] == 'DATOS_VACIOS'

    def test_optimizar_ruta_sin_content_type_json(self):
        """Prueba sin enviar Content-Type application/json"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        resp = client.post('/ruta-optima', 
                          data=str(payload),  # Enviar como string, no JSON
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'error' in resp.get_json()
        assert 'Content-Type' in resp.get_json()['error']

    def test_optimizar_ruta_datos_invalidos(self):
        """Prueba con datos inválidos"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {}  # Datos vacíos

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=LogisticaServiceError({'error': 'Datos inválidos', 'codigo': 'DATOS_VACIOS'}, 400)):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_sin_bodega(self):
        """Prueba sin campo bodega"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'destinos': [[-74.0445, 4.6760]]
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=LogisticaServiceError({'error': 'Campo bodega requerido', 'codigo': 'BODEGA_REQUERIDA'}, 400)):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_sin_destinos(self):
        """Prueba sin campo destinos"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110]
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=LogisticaServiceError({'error': 'Campo destinos requerido', 'codigo': 'DESTINOS_REQUERIDOS'}, 400)):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_service_error_500(self):
        """Prueba cuando el servicio retorna error 500"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=LogisticaServiceError({'error': 'Error interno', 'codigo': 'ERROR_INTERNO'}, 500)):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_timeout(self):
        """Prueba cuando ocurre timeout"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=LogisticaServiceError({'error': 'Timeout', 'codigo': 'TIMEOUT'}, 504)):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 504
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_connection_error(self):
        """Prueba cuando no se puede conectar al servicio"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=LogisticaServiceError({'error': 'Error de conexión', 'codigo': 'ERROR_CONEXION'}, 503)):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 503
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_unexpected_error(self):
        """Prueba cuando ocurre un error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [[-74.0445, 4.6760]]
        }

        with patch('src.blueprints.logistica.optimizar_ruta', 
                   side_effect=Exception('Error inesperado')):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_optimizar_ruta_multiples_destinos(self):
        """Prueba con múltiples destinos"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        payload = {
            'bodega': [-74.0721, 4.7110],
            'destinos': [
                [-74.0445, 4.6760],
                [-74.0817, 4.6097],
                [-74.1000, 4.6500],
                [-74.0500, 4.7000],
                [-74.1200, 4.6800]
            ]
        }

        ruta_optima = {
            'ruta_optima': [
                [-74.0721, 4.7110],
                [-74.0500, 4.7000],
                [-74.0445, 4.6760],
                [-74.1000, 4.6500],
                [-74.1200, 4.6800],
                [-74.0817, 4.6097]
            ],
            'distancia_total': 25.8,
            'tiempo_estimado': 75
        }

        with patch('src.blueprints.logistica.optimizar_ruta', return_value=ruta_optima):
            resp = client.post('/ruta-optima', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['ruta_optima']) == 6
        assert data['distancia_total'] == 25.8
        assert data['tiempo_estimado'] == 75
