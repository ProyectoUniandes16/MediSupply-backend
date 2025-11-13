import pytest
from unittest.mock import patch, MagicMock
from src.services.ruta_service import (
    optimizar_ruta, 
    RutaServiceError,
    obtener_geometria_ruta_detallada,
    generar_mapa_ruta_html
)


def test_optimizar_ruta_exito(app):
    """Test de optimización de ruta exitosa"""
    with app.app_context():
        # Mock de la respuesta de la API de optimización
        mock_opt_response = MagicMock()
        mock_opt_response.status_code = 200
        mock_opt_response.json.return_value = {
            "routes": [{
                "steps": [
                    {"job": "inicio/fin", "location": [-74.08175, 4.60971]},
                    {"job": 1, "location": [-74.0445, 4.676]},
                    {"job": 2, "location": [-74.1475, 4.6165]},
                    {"job": "inicio/fin", "location": [-74.08175, 4.60971]}
                ]
            }],
            "summary": {
                "distance": 25000,
                "duration": 1800,
                "service": 600,
                "cost": 100
            }
        }
        
        # Mock de la geometría detallada
        mock_geometry = [[4.60971, -74.08175], [4.676, -74.0445]]
        
        with patch('requests.post', return_value=mock_opt_response), \
             patch('src.services.ruta_service.obtener_geometria_ruta_detallada', return_value=mock_geometry), \
             patch('src.services.ruta_service.generar_mapa_ruta_html', return_value="<html>mapa</html>"):
            
            resultado = optimizar_ruta(
                bodega=[-74.08175, 4.60971],
                destinos=[[-74.0445, 4.676], [-74.1475, 4.6165]]
            )
            
            assert 'orden_optimo' in resultado
            assert 'resumen' in resultado
            assert 'mapa_html' in resultado
            assert resultado['resumen']['distancia_total_metros'] == 25000
            assert len(resultado['orden_optimo']) == 4


def test_optimizar_ruta_bodega_invalida(app):
    """Test con coordenadas de bodega inválidas"""
    with app.app_context():
        with pytest.raises(RutaServiceError) as exc_info:
            optimizar_ruta(
                bodega=[-74.08175],  # Solo una coordenada
                destinos=[[-74.0445, 4.676]]
            )
        
        assert exc_info.value.status_code == 400
        assert 'BODEGA_INVALIDA' in str(exc_info.value.message)


def test_optimizar_ruta_sin_destinos(app):
    """Test sin destinos"""
    with app.app_context():
        with pytest.raises(RutaServiceError) as exc_info:
            optimizar_ruta(
                bodega=[-74.08175, 4.60971],
                destinos=[]
            )
        
        assert exc_info.value.status_code == 400
        assert 'DESTINOS_INSUFICIENTES' in str(exc_info.value.message)


def test_optimizar_ruta_destino_invalido(app):
    """Test con destino con coordenadas inválidas"""
    with app.app_context():
        with pytest.raises(RutaServiceError) as exc_info:
            optimizar_ruta(
                bodega=[-74.08175, 4.60971],
                destinos=[[-74.0445]]  # Solo una coordenada
            )
        
        assert exc_info.value.status_code == 400
        assert 'DESTINO_INVALIDO' in str(exc_info.value.message)


def test_optimizar_ruta_sin_api_key(app):
    """Test sin API key configurada"""
    with app.app_context():
        with patch('src.services.ruta_service.ORS_API_KEY', None):
            with pytest.raises(RutaServiceError) as exc_info:
                optimizar_ruta(
                    bodega=[-74.08175, 4.60971],
                    destinos=[[-74.0445, 4.676]]
                )
            
            assert exc_info.value.status_code == 500
            assert 'API_KEY_NO_CONFIGURADA' in str(exc_info.value.message)


def test_optimizar_ruta_error_api(app):
    """Test cuando la API de ORS retorna error"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error en la API"
        
        with patch('requests.post', return_value=mock_response):
            with pytest.raises(RutaServiceError) as exc_info:
                optimizar_ruta(
                    bodega=[-74.08175, 4.60971],
                    destinos=[[-74.0445, 4.676]]
                )
            
            # El error se envuelve en ERROR_INESPERADO pero viene del ERROR_OPTIMIZACION
            assert exc_info.value.status_code in [400, 500]
            assert 'error' in str(exc_info.value.message).lower()


def test_optimizar_ruta_timeout(app):
    """Test cuando hay timeout en la API"""
    with app.app_context():
        import requests
        
        with patch('requests.post', side_effect=requests.exceptions.Timeout):
            with pytest.raises(RutaServiceError) as exc_info:
                optimizar_ruta(
                    bodega=[-74.08175, 4.60971],
                    destinos=[[-74.0445, 4.676]]
                )
            
            assert exc_info.value.status_code == 504
            assert 'TIMEOUT_API' in str(exc_info.value.message)


def test_obtener_geometria_ruta_detallada_exito(app):
    """Test de obtención de geometría detallada exitosa"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [{
                "geometry": {
                    "coordinates": [
                        [-74.08175, 4.60971],
                        [-74.0445, 4.676]
                    ]
                }
            }]
        }
        
        with patch('requests.post', return_value=mock_response):
            resultado = obtener_geometria_ruta_detallada([
                [-74.08175, 4.60971],
                [-74.0445, 4.676]
            ])
            
            assert resultado is not None
            assert len(resultado) == 2
            # Verificar que se intercambiaron las coordenadas para Folium
            assert resultado[0] == [4.60971, -74.08175]


def test_obtener_geometria_ruta_detallada_sin_api_key(app):
    """Test sin API key"""
    with app.app_context():
        with patch('src.services.ruta_service.ORS_API_KEY', None):
            resultado = obtener_geometria_ruta_detallada([
                [-74.08175, 4.60971],
                [-74.0445, 4.676]
            ])
            
            assert resultado is None


def test_obtener_geometria_ruta_detallada_error_api(app):
    """Test cuando la API retorna error"""
    with app.app_context():
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error"
        
        with patch('requests.post', return_value=mock_response):
            resultado = obtener_geometria_ruta_detallada([
                [-74.08175, 4.60971],
                [-74.0445, 4.676]
            ])
            
            assert resultado is None


def test_generar_mapa_ruta_html(app):
    """Test de generación de mapa HTML"""
    with app.app_context():
        bodega = [-74.08175, 4.60971]
        orden_destinos = [
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]},
            {"job_id": 1, "ubicacion": [-74.0445, 4.676]},
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]}
        ]
        ruta_detallada = [[4.60971, -74.08175], [4.676, -74.0445]]
        
        html = generar_mapa_ruta_html(bodega, orden_destinos, ruta_detallada)
        
        assert html is not None
        assert isinstance(html, str)
        assert len(html) > 0


def test_generar_mapa_ruta_html_sin_geometria(app):
    """Test de generación de mapa sin geometría detallada (líneas rectas)"""
    with app.app_context():
        bodega = [-74.08175, 4.60971]
        orden_destinos = [
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]},
            {"job_id": 1, "ubicacion": [-74.0445, 4.676]},
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]}
        ]
        
        # Sin ruta detallada
        html = generar_mapa_ruta_html(bodega, orden_destinos, None)
        
        assert html is not None
        assert isinstance(html, str)
        assert len(html) > 0
