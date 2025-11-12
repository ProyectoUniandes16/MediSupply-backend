import pytest
import json
from unittest.mock import patch, MagicMock


def test_ruta_optima_exito_formato_json(client):
    """Test de optimización de ruta exitosa con formato JSON"""
    mock_response = {
        "orden_optimo": [
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]},
            {"job_id": 1, "ubicacion": [-74.0445, 4.676]},
            {"job_id": 2, "ubicacion": [-74.1475, 4.6165]},
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]}
        ],
        "resumen": {
            "distancia_total_metros": 25000,
            "tiempo_total_segundos": 1800,
            "tiempo_servicio_segundos": 600,
            "costo": 100
        },
        "mapa_html": "<html>mapa</html>"
    }
    
    with patch('src.blueprints.rutas.optimizar_ruta', return_value=mock_response):
        data = {
            "bodega": [-74.08175, 4.60971],
            "destinos": [
                [-74.0445, 4.676],
                [-74.1475, 4.6165]
            ]
        }
        
        response = client.post('/ruta-optima?formato=json',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'orden_optimo' in json_data
        assert 'resumen' in json_data
        assert 'mensaje' in json_data
        assert json_data['resumen']['distancia_total_metros'] == 25000


def test_ruta_optima_exito_formato_html(client):
    """Test de optimización de ruta exitosa con formato HTML"""
    mock_response = {
        "orden_optimo": [
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]},
            {"job_id": 1, "ubicacion": [-74.0445, 4.676]}
        ],
        "resumen": {
            "distancia_total_metros": 10000,
            "tiempo_total_segundos": 900,
            "tiempo_servicio_segundos": 300,
            "costo": 50
        },
        "mapa_html": "<html><body>Mapa HTML</body></html>"
    }
    
    with patch('src.blueprints.rutas.optimizar_ruta', return_value=mock_response):
        data = {
            "bodega": [-74.08175, 4.60971],
            "destinos": [[-74.0445, 4.676]]
        }
        
        response = client.post('/ruta-optima',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        assert 'text/html' in response.content_type
        assert b'Ruta' in response.data  # Verificar que contiene contenido HTML
        assert b'min' in response.data  # Verificar estadísticas de tiempo


def test_ruta_optima_sin_bodega(client):
    """Test sin coordenadas de bodega"""
    data = {
        "destinos": [[-74.0445, 4.676]]
    }
    
    response = client.post('/ruta-optima?formato=json',
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data


def test_ruta_optima_sin_destinos(client):
    """Test sin destinos"""
    data = {
        "bodega": [-74.08175, 4.60971]
    }
    
    response = client.post('/ruta-optima?formato=json',
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data


def test_ruta_optima_bodega_invalida(client):
    """Test con coordenadas de bodega inválidas"""
    data = {
        "bodega": [-74.08175],  # Solo una coordenada
        "destinos": [[-74.0445, 4.676]]
    }
    
    response = client.post('/ruta-optima?formato=json',
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data


def test_ruta_optima_destino_invalido(client):
    """Test con coordenadas de destino inválidas"""
    data = {
        "bodega": [-74.08175, 4.60971],
        "destinos": [[-74.0445]]  # Solo una coordenada
    }
    
    response = client.post('/ruta-optima?formato=json',
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data


def test_ruta_optima_sin_json_body(client):
    """Test sin body JSON"""
    response = client.post('/ruta-optima?formato=json',
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data


def test_ruta_optima_error_servicio(client):
    """Test cuando el servicio lanza una excepción"""
    from src.services.ruta_service import RutaServiceError
    
    with patch('src.blueprints.rutas.optimizar_ruta', 
               side_effect=RutaServiceError({'error': 'Error test', 'codigo': 'TEST_ERROR'}, 500)):
        data = {
            "bodega": [-74.08175, 4.60971],
            "destinos": [[-74.0445, 4.676]]
        }
        
        response = client.post('/ruta-optima?formato=json',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 500
        json_data = response.get_json()
        assert 'error' in json_data
