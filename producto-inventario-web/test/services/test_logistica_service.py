import pytest
from unittest.mock import patch, MagicMock
import requests

from src.services.logistica import listar_zonas, obtener_zona_detallada, LogisticaServiceError


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
