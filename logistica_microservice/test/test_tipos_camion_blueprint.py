import pytest
import json


def test_listar_tipos_camion_endpoint(client, access_token):
    """Test del endpoint para listar tipos de camión"""
    from src.services.tipo_camion_service import crear_tipo_camion
    
    # Crear algunos tipos
    crear_tipo_camion({'nombre': 'Tipo A', 'descripcion': 'Desc A'})
    crear_tipo_camion({'nombre': 'Tipo B', 'descripcion': 'Desc B'})
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/tipo-camion', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'data' in json_data
    assert 'total' in json_data


def test_crear_tipo_camion_endpoint(client, access_token):
    """Test del endpoint para crear tipo de camión"""
    data = {
        'nombre': 'Nuevo Tipo',
        'descripcion': 'Nueva descripción'
    }
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/tipo-camion',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['nombre'] == 'Nuevo Tipo'


def test_crear_tipo_camion_error_validacion(client, access_token):
    """Test de error de validación al crear tipo"""
    data = {}  # Falta nombre
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/tipo-camion',
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')
    
    assert response.status_code == 400


def test_obtener_tipo_camion_endpoint(client, access_token):
    """Test del endpoint para obtener tipo por ID"""
    from src.services.tipo_camion_service import crear_tipo_camion
    
    tipo = crear_tipo_camion({'nombre': 'Tipo Obtener'})
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(f'/tipo-camion/{tipo["id"]}', headers=headers)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['id'] == tipo['id']


def test_obtener_tipo_camion_no_encontrado(client, access_token):
    """Test de obtener tipo no encontrado"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/tipo-camion/id-inexistente', headers=headers)
    
    assert response.status_code == 404


def test_crear_tipo_camion_exception_generica(client, access_token):
    """Test de manejo de excepción genérica"""
    from unittest.mock import patch
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.tipos_camion.crear_tipo_camion') as mock_crear:
        mock_crear.side_effect = Exception('Error inesperado')
        
        data = {'nombre': 'Test'}
        response = client.post('/tipo-camion',
                              data=json.dumps(data),
                              headers=headers,
                              content_type='application/json')
        
        assert response.status_code == 500


def test_listar_tipos_camion_exception_generica(client, access_token):
    """Test de excepción en listar tipos"""
    from unittest.mock import patch
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.tipos_camion.listar_tipos_camion') as mock_listar:
        mock_listar.side_effect = Exception('Error inesperado')
        
        response = client.get('/tipo-camion', headers=headers)
        assert response.status_code == 500


def test_obtener_tipo_camion_exception_generica(client, access_token):
    """Test de excepción en obtener tipo"""
    from unittest.mock import patch
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.tipos_camion.obtener_tipo_camion') as mock_obtener:
        mock_obtener.side_effect = Exception('Error inesperado')
        
        response = client.get('/tipo-camion/test-id', headers=headers)
        assert response.status_code == 500


def test_inicializar_tipos_exception_generica(client, access_token):
    """Test de excepción en inicializar tipos"""
    from unittest.mock import patch
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    with patch('src.blueprints.tipos_camion.inicializar_tipos_camion') as mock_init:
        mock_init.side_effect = Exception('Error inesperado')
        
        response = client.post('/tipo-camion/inicializar', headers=headers)
        assert response.status_code == 500
