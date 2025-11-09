import pytest
import json
from unittest.mock import patch
from src.services.zona_service import ZonaServiceError
from src.services.bodega_service import BodegaServiceError


def test_zona_service_error_handling(client, access_token):
    """Test manejo de errores del servicio de zonas en el endpoint"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Test con datos inválidos que generan ZonaServiceError
    data = {
        'nombre': 'Zona Test',
        'latitud_maxima': 200.0,  # Inválido
        'latitud_minima': 5.0,
        'longitud_maxima': -70.0,
        'longitud_minima': -75.0
    }
    
    response = client.post('/zona',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 400


def test_zona_exception_generica(client, access_token):
    """Test manejo de excepción genérica en endpoint de zonas"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.zonas.crear_zona') as mock_crear:
        mock_crear.side_effect = Exception('Error inesperado')
        
        data = {
            'nombre': 'Zona Test',
            'latitud_maxima': 10.0,
            'latitud_minima': 5.0,
            'longitud_maxima': -70.0,
            'longitud_minima': -75.0
        }
        
        response = client.post('/zona',
                              data=json.dumps(data),
                              headers=headers,
                              content_type='application/json')
        
        assert response.status_code == 500


def test_bodega_service_error_handling(client, access_token):
    """Test manejo de errores del servicio de bodegas en el endpoint"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Test con zona inexistente que genera BodegaServiceError
    data = {
        'nombre': 'Bodega Test',
        'ubicacion': 'Test',
        'zona_id': 'id-inexistente'
    }
    
    response = client.post('/bodega',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 404


def test_bodega_exception_generica(client, access_token):
    """Test manejo de excepción genérica en endpoint de bodegas"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.bodegas.crear_bodega') as mock_crear:
        mock_crear.side_effect = Exception('Error inesperado')
        
        data = {
            'nombre': 'Bodega Test',
            'ubicacion': 'Test',
            'zona_id': 'test-id'
        }
        
        response = client.post('/bodega',
                              data=json.dumps(data),
                              headers=headers,
                              content_type='application/json')
        
        assert response.status_code == 500


def test_listar_zonas_exception_generica(client, access_token):
    """Test manejo de excepción genérica en listar zonas"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.zonas.listar_zonas') as mock_listar:
        mock_listar.side_effect = Exception('Error inesperado')
        
        response = client.get('/zona', headers=headers)
        
        assert response.status_code == 500


def test_listar_bodegas_exception_generica(client, access_token):
    """Test manejo de excepción genérica en listar bodegas"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.bodegas.listar_bodegas') as mock_listar:
        mock_listar.side_effect = Exception('Error inesperado')
        
        response = client.get('/bodega', headers=headers)
        
        assert response.status_code == 500


def test_obtener_zona_exception_generica(client, access_token):
    """Test manejo de excepción genérica en obtener zona"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.zonas.obtener_zona') as mock_obtener:
        mock_obtener.side_effect = Exception('Error inesperado')
        
        response = client.get('/zona/test-id', headers=headers)
        
        assert response.status_code == 500


def test_obtener_bodega_exception_generica(client, access_token):
    """Test manejo de excepción genérica en obtener bodega"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.bodegas.obtener_bodega') as mock_obtener:
        mock_obtener.side_effect = Exception('Error inesperado')
        
        response = client.get('/bodega/test-id', headers=headers)
        
        assert response.status_code == 500


def test_listar_zonas_con_bodegas_exception_generica(client, access_token):
    """Test manejo de excepción genérica en listar zonas con bodegas"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.zonas.listar_zonas_con_bodegas') as mock_listar:
        mock_listar.side_effect = Exception('Error inesperado')
        
        response = client.get('/zona-con-bodegas', headers=headers)
        
        assert response.status_code == 500
