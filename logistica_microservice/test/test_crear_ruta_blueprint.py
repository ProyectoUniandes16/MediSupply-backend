import pytest
import json
from unittest.mock import patch, MagicMock
from src.models.ruta import Ruta, DetalleRuta
from src.models.zona import Zona
from src.models.bodega import Bodega
from src.models.camion import Camion
from src.models.tipo_camion import TipoCamion


class TestCrearRutaBlueprint:
    """Pruebas para el endpoint POST /rutas"""

    def test_crear_ruta_exitosa(self, client, app):
        """Test de creación de ruta exitosa"""
        with app.app_context():
            # Crear datos de prueba
            tipo_camion = TipoCamion(nombre="Refrigerado", descripcion="Camión con refrigeración").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Calle 1").save()
            
            camion = Camion(placa="ABC-123", capacidad_kg=1000, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "20f7a15a-069e-4019-afbd-dae3ca0914a1"
                    },
                    {
                        "ubicacion": [-74.0445, 4.6760],
                        "pedido_id": "30f7a15a-069e-4019-afbd-dae3ca0914a2"
                    },
                    {
                        "ubicacion": [-74.1253, 4.7010],
                        "pedido_id": "40f7a15a-069e-4019-afbd-dae3ca0914a3"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": camion.id,
                "zona_id": zona.id,
                "estado": "iniciado"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 201
            json_data = response.get_json()
            assert 'mensaje' in json_data
            assert 'ruta' in json_data
            assert json_data['ruta']['estado'] == 'iniciado'
            assert json_data['ruta']['bodega_id'] == bodega.id
            assert json_data['ruta']['camion_id'] == camion.id
            assert json_data['ruta']['zona_id'] == zona.id
            assert len(json_data['ruta']['detalles']) == 3
            
            # Verificar orden de los detalles
            for i, detalle in enumerate(json_data['ruta']['detalles'], start=1):
                assert detalle['orden'] == i
                assert 'ubicacion' in detalle
                assert 'pedido_id' in detalle

    def test_crear_ruta_estado_pendiente(self, client, app):
        """Test de creación de ruta con estado pendiente"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Sin Refrigeración", descripcion="Test").save()
            
            zona = Zona(nombre="Zona 2", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega 2", ubicacion="Calle 2").save()
            
            camion = Camion(placa="XYZ-789", capacidad_kg=800, capacidad_m3=10, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "50f7a15a-069e-4019-afbd-dae3ca0914a4"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": camion.id,
                "zona_id": zona.id,
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 201
            json_data = response.get_json()
            assert json_data['ruta']['estado'] == 'pendiente'
            assert json_data['ruta']['fecha_inicio'] is None  # No debe tener fecha de inicio

    def test_crear_ruta_sin_datos(self, client):
        """Test sin enviar datos en el body"""
        response = client.post('/rutas',
                              data=json.dumps({}),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'DATOS_FALTANTES'

    def test_crear_ruta_campos_faltantes(self, client):
        """Test con campos requeridos faltantes"""
        data = {
            "ruta": [
                {
                    "ubicacion": [-74.1475, 4.6165],
                    "pedido_id": "test-id"
                }
            ],
            "bodega_id": "test-bodega"
            # Faltan camion_id, zona_id, estado
        }
        
        response = client.post('/rutas',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'CAMPOS_REQUERIDOS'
        assert 'campos_faltantes' in json_data

    def test_crear_ruta_array_vacio(self, client):
        """Test con array de ruta vacío"""
        data = {
            "ruta": [],
            "bodega_id": "test-bodega",
            "camion_id": "test-camion",
            "zona_id": "test-zona",
            "estado": "pendiente"
        }
        
        response = client.post('/rutas',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'RUTA_INVALIDA'

    def test_crear_ruta_punto_sin_ubicacion(self, client):
        """Test con punto de ruta sin campo ubicacion"""
        data = {
            "ruta": [
                {
                    "pedido_id": "test-id"
                    # Falta ubicacion
                }
            ],
            "bodega_id": "test-bodega",
            "camion_id": "test-camion",
            "zona_id": "test-zona",
            "estado": "pendiente"
        }
        
        response = client.post('/rutas',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'PUNTO_RUTA_INVALIDO'

    def test_crear_ruta_punto_sin_pedido_id(self, client):
        """Test con punto de ruta sin campo pedido_id"""
        data = {
            "ruta": [
                {
                    "ubicacion": [-74.1475, 4.6165]
                    # Falta pedido_id
                }
            ],
            "bodega_id": "test-bodega",
            "camion_id": "test-camion",
            "zona_id": "test-zona",
            "estado": "pendiente"
        }
        
        response = client.post('/rutas',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'PUNTO_RUTA_INVALIDO'

    def test_crear_ruta_ubicacion_invalida(self, client):
        """Test con ubicación en formato incorrecto"""
        data = {
            "ruta": [
                {
                    "ubicacion": [-74.1475],  # Solo una coordenada
                    "pedido_id": "test-id"
                }
            ],
            "bodega_id": "test-bodega",
            "camion_id": "test-camion",
            "zona_id": "test-zona",
            "estado": "pendiente"
        }
        
        response = client.post('/rutas',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'UBICACION_INVALIDA'

    def test_crear_ruta_estado_invalido(self, client):
        """Test con estado no permitido"""
        data = {
            "ruta": [
                {
                    "ubicacion": [-74.1475, 4.6165],
                    "pedido_id": "test-id"
                }
            ],
            "bodega_id": "test-bodega",
            "camion_id": "test-camion",
            "zona_id": "test-zona",
            "estado": "estado_invalido"
        }
        
        response = client.post('/rutas',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert json_data['codigo'] == 'ESTADO_INVALIDO'
        assert 'estados_validos' in json_data

    def test_crear_ruta_bodega_no_existe(self, client):
        """Test con bodega que no existe"""
        with patch('src.services.ruta_service.Bodega') as mock_bodega:
            mock_bodega.query.get.return_value = None
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "test-id"
                    }
                ],
                "bodega_id": "bodega-inexistente",
                "camion_id": "test-camion",
                "zona_id": "test-zona",
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 404
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['codigo'] == 'BODEGA_NO_ENCONTRADA'

    def test_crear_ruta_camion_no_existe(self, client, app):
        """Test con camión que no existe"""
        with app.app_context():
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Calle 1").save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "test-id"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": "camion-inexistente",
                "zona_id": zona.id,
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 404
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['codigo'] == 'CAMION_NO_ENCONTRADO'

    def test_crear_ruta_zona_no_existe(self, client, app):
        """Test con zona que no existe"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Calle 1").save()
            
            camion = Camion(placa="ABC-123", capacidad_kg=900, capacidad_m3=11, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "test-id"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": camion.id,
                "zona_id": "zona-inexistente",
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 404
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['codigo'] == 'ZONA_NO_ENCONTRADA'

    def test_crear_ruta_camion_no_disponible(self, client, app):
        """Test con camión que no está disponible"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Calle 1").save()
            
            # Camión NO disponible
            camion = Camion(placa="DEF-456", capacidad_kg=950, capacidad_m3=13, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id, estado='mantenimiento').save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "test-id"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": camion.id,
                "zona_id": zona.id,
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 400
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['codigo'] == 'CAMION_NO_DISPONIBLE'

    def test_crear_ruta_multiples_pedidos_diferentes(self, client, app):
        """Test con múltiples pedidos diferentes en la misma ruta"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Refrigerado", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Calle 1").save()
            
            camion = Camion(placa="GHI-789", capacidad_kg=1200, capacidad_m3=15, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "pedido-001"
                    },
                    {
                        "ubicacion": [-74.0445, 4.6760],
                        "pedido_id": "pedido-002"
                    },
                    {
                        "ubicacion": [-74.1253, 4.7010],
                        "pedido_id": "pedido-003"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": camion.id,
                "zona_id": zona.id,
                "estado": "iniciado"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 201
            json_data = response.get_json()
            assert len(json_data['ruta']['detalles']) == 3
            
            # Verificar que cada detalle tiene su pedido_id correcto
            assert json_data['ruta']['detalles'][0]['pedido_id'] == "pedido-001"
            assert json_data['ruta']['detalles'][1]['pedido_id'] == "pedido-002"
            assert json_data['ruta']['detalles'][2]['pedido_id'] == "pedido-003"

    def test_crear_ruta_verifica_orden_secuencial(self, client, app):
        """Test que verifica que el orden es secuencial según el array"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0, 
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Calle 1").save()
            
            camion = Camion(placa="JKL-012", capacidad_kg=1100, capacidad_m3=14, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "primer-punto"
                    },
                    {
                        "ubicacion": [-74.0445, 4.6760],
                        "pedido_id": "segundo-punto"
                    },
                    {
                        "ubicacion": [-74.1253, 4.7010],
                        "pedido_id": "tercer-punto"
                    },
                    {
                        "ubicacion": [-74.0845, 4.6560],
                        "pedido_id": "cuarto-punto"
                    }
                ],
                "bodega_id": bodega.id,
                "camion_id": camion.id,
                "zona_id": zona.id,
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 201
            json_data = response.get_json()
            detalles = json_data['ruta']['detalles']
            
            # Verificar que el orden es 1, 2, 3, 4
            for i, detalle in enumerate(detalles, start=1):
                assert detalle['orden'] == i

    def test_crear_ruta_error_inesperado(self, client):
        """Test cuando ocurre un error inesperado en el servicio"""
        with patch('src.blueprints.rutas.crear_ruta_entrega', 
                   side_effect=Exception('Error de base de datos')):
            data = {
                "ruta": [
                    {
                        "ubicacion": [-74.1475, 4.6165],
                        "pedido_id": "test-id"
                    }
                ],
                "bodega_id": "test-bodega",
                "camion_id": "test-camion",
                "zona_id": "test-zona",
                "estado": "pendiente"
            }
            
            response = client.post('/rutas',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['codigo'] == 'ERROR_INTERNO_SERVIDOR'
