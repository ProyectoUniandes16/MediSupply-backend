import pytest
from unittest.mock import patch, MagicMock
from src.services.ruta_service import crear_ruta_entrega, RutaServiceError
from src.models.ruta import Ruta, DetalleRuta
from src.models.zona import Zona, db
from src.models.bodega import Bodega
from src.models.camion import Camion
from src.models.tipo_camion import TipoCamion


class TestCrearRutaEntregaService:
    """Pruebas para el servicio crear_ruta_entrega"""

    def test_crear_ruta_exitosa(self, app):
        """Test de creación exitosa de una ruta"""
        with app.app_context():
            # Crear datos de prueba
            tipo_camion = TipoCamion(nombre="Refrigerado", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Central", ubicacion="Av. Principal 123").save()
            
            camion = Camion(placa="ABC-123", capacidad_kg=1000, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            puntos_ruta = [
                {
                    "ubicacion": [-74.1475, 4.6165],
                    "pedido_id": "pedido-001"
                },
                {
                    "ubicacion": [-74.0445, 4.6760],
                    "pedido_id": "pedido-002"
                }
            ]
            
            # Crear la ruta
            ruta = crear_ruta_entrega(
                bodega_id=bodega.id,
                camion_id=camion.id,
                zona_id=zona.id,
                estado="pendiente",
                puntos_ruta=puntos_ruta
            )
            
            # Verificaciones
            assert ruta is not None
            assert ruta.bodega_id == bodega.id
            assert ruta.camion_id == camion.id
            assert ruta.zona_id == zona.id
            assert ruta.estado == "pendiente"
            
            # Verificar detalles
            detalles = ruta.detalles.all()
            assert len(detalles) == 2
            assert detalles[0].orden == 1
            assert detalles[1].orden == 2

    def test_crear_ruta_estado_iniciado(self, app):
        """Test de creación de ruta con estado iniciado"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Sin Refrigeración", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Norte", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Norte", ubicacion="Calle 50").save()
            
            camion = Camion(placa="XYZ-789", capacidad_kg=800, capacidad_m3=10, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            puntos_ruta = [
                {
                    "ubicacion": [-74.1, 4.65],
                    "pedido_id": "pedido-100"
                }
            ]
            
            # Crear la ruta con estado iniciado
            ruta = crear_ruta_entrega(
                bodega_id=bodega.id,
                camion_id=camion.id,
                zona_id=zona.id,
                estado="iniciado",
                puntos_ruta=puntos_ruta
            )
            
            # Verificaciones
            assert ruta.estado == "iniciado"
            assert ruta.fecha_inicio is not None
            
            # Verificar que el camión ya no está disponible
            camion_actualizado = Camion.query.get(camion.id)
            assert camion_actualizado.disponible is False

    def test_crear_ruta_estado_en_progreso_marca_camion_no_disponible(self, app):
        """Test que verifica que estado en_progreso marca el camión como no disponible"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Mixto", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Sur", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Sur", ubicacion="Calle 10").save()
            
            camion = Camion(placa="DEF-456", capacidad_kg=850, capacidad_m3=11, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            puntos_ruta = [
                {
                    "ubicacion": [-74.08, 4.60],
                    "pedido_id": "pedido-200"
                }
            ]
            
            # Crear la ruta
            ruta = crear_ruta_entrega(
                bodega_id=bodega.id,
                camion_id=camion.id,
                zona_id=zona.id,
                estado="en_progreso",
                puntos_ruta=puntos_ruta
            )
            
            # Verificar que el camión no está disponible
            assert ruta is not None
            assert ruta.estado == 'en_progreso'
            camion_actualizado = Camion.query.get(camion.id)
            assert camion_actualizado.estado == 'en_ruta'

    def test_crear_ruta_bodega_no_existe(self, app):
        """Test con bodega que no existe"""
        with app.app_context():
            with pytest.raises(RutaServiceError) as exc_info:
                crear_ruta_entrega(
                    bodega_id="bodega-inexistente",
                    camion_id="camion-test",
                    zona_id="zona-test",
                    estado="pendiente",
                    puntos_ruta=[
                        {
                            "ubicacion": [-74.1, 4.6],
                            "pedido_id": "test"
                        }
                    ]
                )
            
            assert exc_info.value.status_code == 404
            assert "bodega" in exc_info.value.message['error'].lower()

    def test_crear_ruta_camion_no_existe(self, app):
        """Test con camión que no existe"""
        with app.app_context():
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            with pytest.raises(RutaServiceError) as exc_info:
                crear_ruta_entrega(
                    bodega_id=bodega.id,
                    camion_id="camion-inexistente",
                    zona_id=zona.id,
                    estado="pendiente",
                    puntos_ruta=[
                        {
                            "ubicacion": [-74.1, 4.6],
                            "pedido_id": "test"
                        }
                    ]
                )
            
            assert exc_info.value.status_code == 404
            assert "camión" in exc_info.value.message['error'].lower()

    def test_crear_ruta_zona_no_existe(self, app):
        """Test con zona que no existe"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Temp", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            camion = Camion(placa="TEST-123", capacidad_kg=900, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            with pytest.raises(RutaServiceError) as exc_info:
                crear_ruta_entrega(
                    bodega_id=bodega.id,
                    camion_id=camion.id,
                    zona_id="zona-inexistente",
                    estado="pendiente",
                    puntos_ruta=[
                        {
                            "ubicacion": [-74.1, 4.6],
                            "pedido_id": "test"
                        }
                    ]
                )
            
            assert exc_info.value.status_code == 404
            assert "zona" in exc_info.value.message['error'].lower()

    def test_crear_ruta_camion_no_disponible(self, app):
        """Test con camión que no está disponible"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            # Camión NO disponible
            camion = Camion(placa="NODIS-123", capacidad_kg=950, capacidad_m3=13, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id, estado='mantenimiento').save()
            
            with pytest.raises(RutaServiceError) as exc_info:
                crear_ruta_entrega(
                    bodega_id=bodega.id,
                    camion_id=camion.id,
                    zona_id=zona.id,
                    estado="pendiente",
                    puntos_ruta=[
                        {
                            "ubicacion": [-74.1, 4.6],
                            "pedido_id": "test"
                        }
                    ]
                )
            
            assert exc_info.value.status_code == 400
            assert "disponible" in exc_info.value.message['error'].lower()

    def test_crear_ruta_multiples_puntos_orden_correcto(self, app):
        """Test que verifica el orden correcto de múltiples puntos"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            camion = Camion(placa="ORDER-123", capacidad_kg=1000, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            puntos_ruta = [
                {"ubicacion": [-74.1, 4.6], "pedido_id": "pedido-1"},
                {"ubicacion": [-74.2, 4.7], "pedido_id": "pedido-2"},
                {"ubicacion": [-74.3, 4.8], "pedido_id": "pedido-3"},
                {"ubicacion": [-74.4, 4.9], "pedido_id": "pedido-4"},
                {"ubicacion": [-74.5, 5.0], "pedido_id": "pedido-5"}
            ]
            
            ruta = crear_ruta_entrega(
                bodega_id=bodega.id,
                camion_id=camion.id,
                zona_id=zona.id,
                estado="pendiente",
                puntos_ruta=puntos_ruta
            )
            
            # Verificar orden
            detalles = ruta.detalles.order_by(DetalleRuta.orden.asc()).all()
            assert len(detalles) == 5
            
            for i, detalle in enumerate(detalles, start=1):
                assert detalle.orden == i
                assert detalle.pedido_id == f"pedido-{i}"

    def test_crear_ruta_verifica_coordenadas_correctas(self, app):
        """Test que verifica que las coordenadas se guardan correctamente"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            camion = Camion(placa="COORD-123", capacidad_kg=1000, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            longitud_esperada = -74.1475
            latitud_esperada = 4.6165
            
            puntos_ruta = [
                {
                    "ubicacion": [longitud_esperada, latitud_esperada],
                    "pedido_id": "test-coordenadas"
                }
            ]
            
            ruta = crear_ruta_entrega(
                bodega_id=bodega.id,
                camion_id=camion.id,
                zona_id=zona.id,
                estado="pendiente",
                puntos_ruta=puntos_ruta
            )
            
            detalle = ruta.detalles.first()
            assert abs(detalle.longitud - longitud_esperada) < 1e-9
            assert abs(detalle.latitud - latitud_esperada) < 1e-9

    def test_crear_ruta_to_dict_with_details(self, app):
        """Test del método to_dict_with_details"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            camion = Camion(placa="DICT-123", capacidad_kg=1000, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            puntos_ruta = [
                {"ubicacion": [-74.1, 4.6], "pedido_id": "p1"},
                {"ubicacion": [-74.2, 4.7], "pedido_id": "p2"}
            ]
            
            ruta = crear_ruta_entrega(
                bodega_id=bodega.id,
                camion_id=camion.id,
                zona_id=zona.id,
                estado="pendiente",
                puntos_ruta=puntos_ruta
            )
            
            # Convertir a dict
            ruta_dict = ruta.to_dict_with_details()
            
            # Verificaciones
            assert 'id' in ruta_dict
            assert 'detalles' in ruta_dict
            assert len(ruta_dict['detalles']) == 2
            assert ruta_dict['estado'] == 'pendiente'
            assert ruta_dict['bodega_id'] == bodega.id
            assert ruta_dict['camion_id'] == camion.id
            assert ruta_dict['zona_id'] == zona.id

    def test_crear_ruta_rollback_en_error(self, app):
        """Test que verifica rollback en caso de error"""
        with app.app_context():
            tipo_camion = TipoCamion(nombre="Test", descripcion="Test").save()
            
            zona = Zona(nombre="Zona Test", latitud_maxima=5.0, latitud_minima=4.0,
                       longitud_maxima=-74.0, longitud_minima=-75.0)
            zona.save()
            
            bodega = Bodega(nombre="Bodega Test", ubicacion="Test").save()
            
            camion = Camion(placa="ERROR-123", capacidad_kg=1000, capacidad_m3=12, bodega_id=bodega.id, tipo_camion_id=tipo_camion.id).save()
            
            # Simular error en el guardado
            with patch.object(DetalleRuta, 'save', side_effect=Exception('Error de BD')):
                with pytest.raises(RutaServiceError) as exc_info:
                    crear_ruta_entrega(
                        bodega_id=bodega.id,
                        camion_id=camion.id,
                        zona_id=zona.id,
                        estado="pendiente",
                        puntos_ruta=[
                            {"ubicacion": [-74.1, 4.6], "pedido_id": "test"}
                        ]
                    )
                
                assert exc_info.value.status_code == 500
                assert "ERROR_CREACION_RUTA" in exc_info.value.message['codigo']
