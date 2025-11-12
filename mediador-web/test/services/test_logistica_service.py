"""
Tests unitarios para el servicio de logística - optimización de rutas.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.logistica import optimizar_ruta, LogisticaServiceError


class TestOptimizarRuta:
    """Tests para optimizar_ruta"""
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_formato_json_exito(self, mock_post):
        """Test: optimizar ruta con formato JSON exitoso"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'orden_optimo': [
                {'job_id': 'inicio/fin', 'ubicacion': [-74.08175, 4.60971]},
                {'job_id': 1, 'ubicacion': [-74.0445, 4.676]},
                {'job_id': 2, 'ubicacion': [-74.1475, 4.6165]},
            ],
            'resumen': {
                'distancia_total_metros': 25000,
                'tiempo_total_segundos': 1800,
            },
            'mensaje': 'Ruta optimizada exitosamente'
        }
        mock_post.return_value = mock_response
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676], [-74.1475, 4.6165]]
        }
        
        # Act
        resultado = optimizar_ruta(payload, formato='json')
        
        # Assert
        assert 'orden_optimo' in resultado
        assert 'resumen' in resultado
        assert len(resultado['orden_optimo']) == 3
        assert resultado['resumen']['distancia_total_metros'] == 25000
        
        # Verificar que se llamó con los parámetros correctos
        args, kwargs = mock_post.call_args
        assert 'ruta-optima' in args[0]
        assert kwargs['json'] == payload
        assert kwargs['params']['formato'] == 'json'
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_formato_html_exito(self, mock_post):
        """Test: optimizar ruta con formato HTML exitoso"""
        # Arrange
        html_content = '<html><body><h1>Mapa de Ruta</h1></body></html>'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_post.return_value = mock_response
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        # Act
        resultado = optimizar_ruta(payload, formato='html')
        
        # Assert
        assert isinstance(resultado, str)
        assert 'Mapa de Ruta' in resultado
        
        # Verificar parámetros
        args, kwargs = mock_post.call_args
        assert kwargs['params']['formato'] == 'html'
    
    def test_optimizar_ruta_sin_datos(self):
        """Test: error cuando no se proporcionan datos"""
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(None)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.message['codigo'] == 'DATOS_VACIOS'
    
    def test_optimizar_ruta_datos_vacios(self):
        """Test: error cuando los datos están vacíos"""
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta({})
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.message['codigo'] == 'DATOS_VACIOS'
    
    def test_optimizar_ruta_sin_bodega(self):
        """Test: error cuando falta el campo bodega"""
        payload = {'destinos': [[-74.0445, 4.676]]}
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.message['codigo'] == 'BODEGA_REQUERIDA'
    
    def test_optimizar_ruta_sin_destinos(self):
        """Test: error cuando falta el campo destinos"""
        payload = {'bodega': [-74.08175, 4.60971]}
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.message['codigo'] == 'DESTINOS_REQUERIDOS'
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_error_http_400(self, mock_post):
        """Test: error HTTP 400 del microservicio"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'Coordenadas inválidas',
            'codigo': 'COORDENADAS_INVALIDAS'
        }
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        import requests
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload)
        
        assert exc_info.value.status_code == 400
        assert 'error' in exc_info.value.message
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_timeout(self, mock_post):
        """Test: timeout al llamar al microservicio"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload)
        
        assert exc_info.value.status_code == 504
        assert exc_info.value.message['codigo'] == 'TIMEOUT'
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_error_conexion(self, mock_post):
        """Test: error de conexión con el microservicio"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload)
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.message['codigo'] == 'ERROR_CONEXION'
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_respuesta_json_invalida(self, mock_post):
        """Test: respuesta sin JSON válido del microservicio"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON")
        mock_post.return_value = mock_response
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload, formato='json')
        
        assert exc_info.value.status_code == 502
        assert exc_info.value.message['codigo'] == 'RESPUESTA_INVALIDA'
    
    @patch('src.services.logistica.requests.post')
    def test_optimizar_ruta_error_inesperado(self, mock_post):
        """Test: error inesperado durante la ejecución"""
        mock_post.side_effect = Exception("Error inesperado")
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        with pytest.raises(LogisticaServiceError) as exc_info:
            optimizar_ruta(payload)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.message['codigo'] == 'ERROR_INESPERADO'
    
    @patch('src.services.logistica.requests.post')
    @patch('src.services.logistica.os.environ.get')
    def test_optimizar_ruta_usa_url_entorno(self, mock_env, mock_post):
        """Test: usa la URL del entorno correctamente"""
        mock_env.return_value = 'http://logistica-service:5013'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'orden_optimo': [], 'resumen': {}}
        mock_post.return_value = mock_response
        
        payload = {
            'bodega': [-74.08175, 4.60971],
            'destinos': [[-74.0445, 4.676]]
        }
        
        optimizar_ruta(payload)
        
        # Verificar que se usó la URL del entorno
        args = mock_post.call_args[0]
        assert 'http://logistica-service:5013/ruta-optima' in args[0]
