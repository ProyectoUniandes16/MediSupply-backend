import pytest
from unittest.mock import patch, MagicMock
import requests

from src.services.logistica import (
    listar_zonas, 
    obtener_zona_detallada, 
    crear_ruta_entrega,
    LogisticaServiceError
)


class TestListarZonas:
    """Pruebas para el servicio listar_zonas"""
    
    def test_listar_zonas_success(self):
        """Prueba exitosa de listado de zonas"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'zonas': [
                {'id': '123', 'nombre': 'México-CDMX', 'pais': 'México'},
                {'id': '456', 'nombre': 'Colombia-Bogotá', 'pais': 'Colombia'}
            ]
        }

        with patch('src.services.logistica.requests.get', return_value=mock_response) as mock_get:
            result = listar_zonas()

        assert result == mock_response.json.return_value
        mock_get.assert_called_once()
        assert '/zona' in mock_get.call_args[0][0]

    def test_listar_zonas_empty_list(self):
        """Prueba cuando no hay zonas"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'zonas': []}

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            result = listar_zonas()

        assert result == {'zonas': []}

    def test_listar_zonas_server_error(self):
        """Prueba cuando el servicio de logística retorna error 500"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                listar_zonas()

        assert excinfo.value.status_code == 500
        assert 'Error al obtener las zonas' in excinfo.value.message

    def test_listar_zonas_not_found(self):
        """Prueba cuando el endpoint no existe (404)"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                listar_zonas()

        assert excinfo.value.status_code == 404

    def test_listar_zonas_timeout(self):
        """Prueba cuando el servicio tarda demasiado en responder"""
        with patch('src.services.logistica.requests.get', side_effect=requests.exceptions.Timeout('Timeout')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                listar_zonas()
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_listar_zonas_connection_error(self):
        """Prueba cuando no se puede conectar al servicio"""
        with patch('src.services.logistica.requests.get', 
                   side_effect=requests.exceptions.ConnectionError('Connection refused')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                listar_zonas()
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_listar_zonas_request_exception(self):
        """Prueba cuando ocurre un error genérico de requests"""
        with patch('src.services.logistica.requests.get', 
                   side_effect=requests.exceptions.RequestException('Generic error')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                listar_zonas()
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message


class TestObtenerZonaDetallada:
    """Pruebas para el servicio obtener_zona_detallada"""
    
    def test_obtener_zona_detallada_success(self):
        """Prueba exitosa de obtención de zona detallada"""
        zona_id = 'zona-123'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
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

        with patch('src.services.logistica.requests.get', return_value=mock_response) as mock_get:
            result = obtener_zona_detallada(zona_id)

        assert result == mock_response.json.return_value
        assert result['id'] == zona_id
        assert len(result['bodegas']) == 1
        assert len(result['camiones']) == 2
        mock_get.assert_called_once()
        assert f'/zona/{zona_id}/detalle' in mock_get.call_args[0][0]

    def test_obtener_zona_detallada_not_found(self):
        """Prueba cuando la zona no existe"""
        zona_id = 'zona-inexistente'
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Zona no encontrada'

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                obtener_zona_detallada(zona_id)

        assert excinfo.value.status_code == 404
        assert 'Zona no encontrada' in excinfo.value.message

    def test_obtener_zona_detallada_server_error(self):
        """Prueba cuando el servicio retorna error 500"""
        zona_id = 'zona-123'
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                obtener_zona_detallada(zona_id)

        assert excinfo.value.status_code == 500

    def test_obtener_zona_detallada_sin_bodegas(self):
        """Prueba zona sin bodegas asociadas"""
        zona_id = 'zona-123'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': zona_id,
            'nombre': 'Test',
            'pais': 'Test',
            'bodegas': [],
            'camiones': []
        }

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            result = obtener_zona_detallada(zona_id)

        assert result['bodegas'] == []
        assert result['camiones'] == []

    def test_obtener_zona_detallada_timeout(self):
        """Prueba cuando el servicio tarda demasiado"""
        zona_id = 'zona-123'
        with patch('src.services.logistica.requests.get', side_effect=requests.exceptions.Timeout('Timeout')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                obtener_zona_detallada(zona_id)
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_obtener_zona_detallada_connection_error(self):
        """Prueba cuando no se puede conectar al servicio"""
        zona_id = 'zona-123'
        with patch('src.services.logistica.requests.get', 
                   side_effect=requests.exceptions.ConnectionError('Connection refused')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                obtener_zona_detallada(zona_id)
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_obtener_zona_detallada_request_exception(self):
        """Prueba cuando ocurre un error genérico"""
        zona_id = 'zona-123'
        with patch('src.services.logistica.requests.get', 
                   side_effect=requests.exceptions.RequestException('Generic error')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                obtener_zona_detallada(zona_id)
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_obtener_zona_detallada_con_uuid(self):
        """Prueba con un UUID válido"""
        zona_id = '550e8400-e29b-41d4-a716-446655440000'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': zona_id,
            'nombre': 'Test Zone',
            'pais': 'Test',
            'bodegas': [],
            'camiones': []
        }

        with patch('src.services.logistica.requests.get', return_value=mock_response):
            result = obtener_zona_detallada(zona_id)

        assert result['id'] == zona_id


class TestLogisticaServiceError:
    """Pruebas para la clase LogisticaServiceError"""
    
    def test_logistica_service_error_creation(self):
        """Prueba creación de excepción personalizada"""
        error = LogisticaServiceError("Test error", 404)
        assert error.message == "Test error"
        assert error.status_code == 404
        assert str(error) == "Test error"


class TestCrearRutaEntrega:
    """Pruebas para el servicio crear_ruta_entrega"""
    
    def test_crear_ruta_entrega_success(self):
        """Prueba exitosa de creación de ruta"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [
                {
                    'ubicacion': [-74.0721, 4.7110],
                    'pedido_id': 'pedido-001'
                },
                {
                    'ubicacion': [-74.0445, 4.6760],
                    'pedido_id': 'pedido-002'
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': '880e8400-e29b-41d4-a716-446655440003',
            'bodega_id': datos_ruta['bodega_id'],
            'camion_id': datos_ruta['camion_id'],
            'zona_id': datos_ruta['zona_id'],
            'estado': 'pendiente',
            'fecha_creacion': '2025-11-13T10:30:00',
            'detalles': [
                {
                    'id': '990e8400-e29b-41d4-a716-446655440004',
                    'orden': 1,
                    'pedido_id': 'pedido-001',
                    'longitud': -74.0721,
                    'latitud': 4.7110
                },
                {
                    'id': 'aa0e8400-e29b-41d4-a716-446655440005',
                    'orden': 2,
                    'pedido_id': 'pedido-002',
                    'longitud': -74.0445,
                    'latitud': 4.6760
                }
            ]
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response) as mock_post:
            result = crear_ruta_entrega(datos_ruta)

        assert result == mock_response.json.return_value
        assert result['estado'] == 'pendiente'
        assert len(result['detalles']) == 2
        mock_post.assert_called_once()
        assert '/rutas' in mock_post.call_args[0][0]
        assert mock_post.call_args[1]['json'] == datos_ruta

    def test_crear_ruta_entrega_bodega_no_encontrada(self):
        """Prueba cuando la bodega no existe"""
        datos_ruta = {
            'bodega_id': 'bodega-inexistente',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'Bodega no encontrada',
            'codigo': 'BODEGA_NO_ENCONTRADA'
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 404
        assert 'Bodega no encontrada' in excinfo.value.message

    def test_crear_ruta_entrega_camion_no_encontrado(self):
        """Prueba cuando el camión no existe"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': 'camion-inexistente',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'Camión no encontrado',
            'codigo': 'CAMION_NO_ENCONTRADO'
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 404
        assert 'Camión no encontrado' in excinfo.value.message

    def test_crear_ruta_entrega_camion_no_disponible(self):
        """Prueba cuando el camión no está disponible"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'El camión no está disponible',
            'codigo': 'CAMION_NO_DISPONIBLE'
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 400
        assert 'no está disponible' in excinfo.value.message

    def test_crear_ruta_entrega_estado_invalido(self):
        """Prueba con estado inválido"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'estado_invalido',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'Estado inválido. Estados permitidos: pendiente, iniciado, en_progreso, completado, cancelado'
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 400
        assert 'Estado inválido' in excinfo.value.message

    def test_crear_ruta_entrega_array_vacio(self):
        """Prueba con array de ruta vacío"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': []
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': "El array 'ruta' no puede estar vacío"
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 400

    def test_crear_ruta_entrega_ubicacion_invalida(self):
        """Prueba con formato de ubicación inválido"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': 'invalido', 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'El campo ubicacion debe ser un array de 2 números [longitud, latitud]'
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 400

    def test_crear_ruta_entrega_server_error(self):
        """Prueba cuando el servicio retorna error 500"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)

        assert excinfo.value.status_code == 500
        assert 'Error al crear la ruta' in excinfo.value.message

    def test_crear_ruta_entrega_timeout(self):
        """Prueba cuando el servicio tarda demasiado en responder"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        with patch('src.services.logistica.requests.post', side_effect=requests.exceptions.Timeout('Timeout')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_crear_ruta_entrega_connection_error(self):
        """Prueba cuando no se puede conectar al servicio"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        with patch('src.services.logistica.requests.post', 
                   side_effect=requests.exceptions.ConnectionError('Connection refused')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_crear_ruta_entrega_request_exception(self):
        """Prueba cuando ocurre un error genérico de requests"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'pendiente',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        with patch('src.services.logistica.requests.post', 
                   side_effect=requests.exceptions.RequestException('Generic error')):
            with pytest.raises(LogisticaServiceError) as excinfo:
                crear_ruta_entrega(datos_ruta)
        
        assert excinfo.value.status_code == 500
        assert 'Error de conexión' in excinfo.value.message

    def test_crear_ruta_entrega_multiples_puntos(self):
        """Prueba creación de ruta con múltiples puntos"""
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
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': '880e8400-e29b-41d4-a716-446655440003',
            'estado': 'pendiente',
            'detalles': [
                {'orden': i+1, 'pedido_id': f'p{i+1}'} 
                for i in range(5)
            ]
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            result = crear_ruta_entrega(datos_ruta)

        assert len(result['detalles']) == 5

    def test_crear_ruta_entrega_estado_iniciado(self):
        """Prueba creación de ruta con estado iniciado"""
        datos_ruta = {
            'bodega_id': '550e8400-e29b-41d4-a716-446655440000',
            'camion_id': '660e8400-e29b-41d4-a716-446655440001',
            'zona_id': '770e8400-e29b-41d4-a716-446655440002',
            'estado': 'iniciado',
            'ruta': [{'ubicacion': [-74.0721, 4.7110], 'pedido_id': 'p1'}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': '880e8400-e29b-41d4-a716-446655440003',
            'estado': 'iniciado',
            'fecha_inicio': '2025-11-13T10:30:00',
            'detalles': [{'orden': 1, 'pedido_id': 'p1'}]
        }

        with patch('src.services.logistica.requests.post', return_value=mock_response):
            result = crear_ruta_entrega(datos_ruta)

        assert result['estado'] == 'iniciado'
        assert 'fecha_inicio' in result
