"""
Tests para las funciones de rutas en logistica_service
"""
import pytest
import requests
from unittest.mock import patch, Mock
from src.services.logistica import (
    listar_rutas_logistica,
    obtener_ruta_detallada,
    LogisticaServiceError
)


class TestListarRutasLogistica:
    """Tests para la función listar_rutas_logistica"""

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_sin_filtros_success(self, mock_config, mock_get):
        """Test listar rutas sin filtros exitosamente"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rutas": [
                {"id": 1, "estado": "pendiente"},
                {"id": 2, "estado": "en_progreso"}
            ]
        }
        mock_get.return_value = mock_response

        result = listar_rutas_logistica()

        assert result == mock_response.json.return_value
        mock_get.assert_called_once_with(
            "http://logistica:5013/rutas",
            params={},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_con_filtro_estado(self, mock_config, mock_get):
        """Test listar rutas con filtro de estado"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rutas": [{"id": 1, "estado": "pendiente"}]}
        mock_get.return_value = mock_response

        result = listar_rutas_logistica(filtros={'estado': 'pendiente'})

        assert result == mock_response.json.return_value
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['estado'] == 'pendiente'

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_con_filtro_zona_id(self, mock_config, mock_get):
        """Test listar rutas con filtro de zona_id"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rutas": []}
        mock_get.return_value = mock_response

        result = listar_rutas_logistica(filtros={'zona_id': 5})

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['zona_id'] == 5

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_con_filtro_camion_id(self, mock_config, mock_get):
        """Test listar rutas con filtro de camion_id"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rutas": []}
        mock_get.return_value = mock_response

        result = listar_rutas_logistica(filtros={'camion_id': 3})

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['camion_id'] == 3

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_con_filtro_bodega_id(self, mock_config, mock_get):
        """Test listar rutas con filtro de bodega_id"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rutas": []}
        mock_get.return_value = mock_response

        result = listar_rutas_logistica(filtros={'bodega_id': 2})

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['bodega_id'] == 2

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_con_multiples_filtros(self, mock_config, mock_get):
        """Test listar rutas con múltiples filtros"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rutas": []}
        mock_get.return_value = mock_response

        result = listar_rutas_logistica(filtros={
            'estado': 'completada',
            'zona_id': 1,
            'camion_id': 2,
            'bodega_id': 3
        })

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['estado'] == 'completada'
        assert call_args[1]['params']['zona_id'] == 1
        assert call_args[1]['params']['camion_id'] == 2
        assert call_args[1]['params']['bodega_id'] == 3

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_error_500(self, mock_config, mock_get):
        """Test listar rutas con error 500"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error interno del servidor"
        mock_get.return_value = mock_response

        with pytest.raises(LogisticaServiceError) as exc_info:
            listar_rutas_logistica()

        assert "Error al obtener las rutas" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_listar_rutas_connection_error(self, mock_config, mock_get):
        """Test listar rutas con error de conexión"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(LogisticaServiceError) as exc_info:
            listar_rutas_logistica()

        assert "Error de conexión" in str(exc_info.value)
        assert exc_info.value.status_code == 500


class TestObtenerRutaDetallada:
    """Tests para la función obtener_ruta_detallada"""

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_obtener_ruta_detallada_success(self, mock_config, mock_get):
        """Test obtener ruta detallada exitosamente"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "estado": "pendiente",
            "detalles": [
                {"orden": 1, "pedido_id": "P001"},
                {"orden": 2, "pedido_id": "P002"}
            ]
        }
        mock_get.return_value = mock_response

        result = obtener_ruta_detallada("1")

        assert result == mock_response.json.return_value
        mock_get.assert_called_once_with(
            "http://logistica:5013/rutas/1",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_obtener_ruta_detallada_not_found(self, mock_config, mock_get):
        """Test obtener ruta detallada que no existe"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(LogisticaServiceError) as exc_info:
            obtener_ruta_detallada("999")

        assert "Ruta no encontrada" in str(exc_info.value)
        assert exc_info.value.status_code == 404

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_obtener_ruta_detallada_error_500(self, mock_config, mock_get):
        """Test obtener ruta detallada con error 500"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error interno"
        mock_get.return_value = mock_response

        with pytest.raises(LogisticaServiceError) as exc_info:
            obtener_ruta_detallada("1")

        assert "Error al obtener la ruta" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_obtener_ruta_detallada_connection_error(self, mock_config, mock_get):
        """Test obtener ruta detallada con error de conexión"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        with pytest.raises(LogisticaServiceError) as exc_info:
            obtener_ruta_detallada("1")

        assert "Error de conexión" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @patch('src.services.logistica.requests.get')
    @patch('src.services.logistica.Config')
    def test_obtener_ruta_detallada_con_uuid(self, mock_config, mock_get):
        """Test obtener ruta detallada con UUID como ID"""
        mock_config.LOGISTICA_URL = "http://logistica:5013"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "550e8400-e29b-41d4-a716-446655440000"}
        mock_get.return_value = mock_response

        result = obtener_ruta_detallada("550e8400-e29b-41d4-a716-446655440000")

        assert result == mock_response.json.return_value
        mock_get.assert_called_once()
