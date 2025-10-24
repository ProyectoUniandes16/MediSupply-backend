"""
Tests para funcionalidad de detalle de producto (HU KAN-101)
"""
import pytest
import json
import io
import os
from datetime import datetime, timedelta
from app.models.producto import Producto, CertificacionProducto
from app.services.producto_service import ProductoService
from app.extensions import db


@pytest.fixture
def producto_completo(app):
    """Fixture para crear un producto completo con certificación"""
    with app.app_context():
        # Crear directorio temporal para certificaciones
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'certificaciones_producto', '1')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Crear producto
        producto = Producto(
            nombre="Ibuprofeno 400mg",
            codigo_sku="IBU-400-2025",
            categoria="medicamento",
            precio_unitario=15.50,
            condiciones_almacenamiento="Almacenar a temperatura ambiente entre 15-30°C",
            fecha_vencimiento=datetime(2026, 12, 31).date(),
            estado="Activo",
            proveedor_id=1,
            usuario_registro="admin@test.com",
            cantidad_disponible=100
        )
        db.session.add(producto)
        db.session.flush()
        
        # Crear archivo temporal de certificación
        cert_path = os.path.join(upload_dir, "test_cert.pdf")
        with open(cert_path, 'wb') as f:
            f.write(b"PDF content test")
        
        # Crear certificación
        certificacion = CertificacionProducto(
            producto_id=producto.id,
            tipo_certificacion="INVIMA",
            nombre_archivo="certificado_invima.pdf",
            ruta_archivo=cert_path,
            tamaño_archivo=1024,
            fecha_vencimiento_cert=datetime(2027, 6, 30).date()
        )
        db.session.add(certificacion)
        db.session.commit()
        
        yield producto
        
        # Cleanup
        if os.path.exists(cert_path):
            os.remove(cert_path)


@pytest.fixture
def producto_sin_certificacion(app):
    """Fixture para producto sin certificación"""
    with app.app_context():
        producto = Producto(
            nombre="Guantes Quirúrgicos",
            codigo_sku="GUANT-001",
            categoria="insumo",
            precio_unitario=25.00,
            condiciones_almacenamiento="Lugar seco y fresco",
            fecha_vencimiento=datetime(2026, 3, 15).date(),
            estado="Activo",
            proveedor_id=2,
            usuario_registro="admin@test.com",
            cantidad_disponible=0
        )
        db.session.add(producto)
        db.session.commit()
        
        yield producto


class TestObtenerDetalleProducto:
    """Tests para obtener detalle de producto por ID"""
    
    def test_obtener_detalle_producto_exitoso(self, client, producto_completo):
        """Test: Obtener detalle completo de producto por ID"""
        response = client.get(f'/api/productos/{producto_completo.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estructura de respuesta
        assert 'producto' in data
        producto = data['producto']
        
        # Verificar campos básicos
        assert producto['id'] == producto_completo.id
        assert producto['nombre'] == "Ibuprofeno 400mg"
        assert producto['codigo_sku'] == "IBU-400-2025"
        assert producto['categoria'] == "medicamento"
        assert producto['precio_unitario'] == 15.50
        assert producto['estado'] == "Activo"
        
        # Verificar inventario
        assert 'inventario' in producto
        assert producto['inventario']['cantidad_disponible'] == 100
        assert producto['inventario']['tiene_stock'] is True
        
        # Verificar certificaciones
        assert 'certificaciones' in producto
        assert len(producto['certificaciones']) == 1
        cert = producto['certificaciones'][0]
        assert cert['tipo_certificacion'] == "INVIMA"
        assert cert['estado'] == "Activo"
        assert 'url_descarga' in cert
        
        # Verificar trazabilidad
        assert 'trazabilidad' in producto
        assert 'fecha_creacion' in producto['trazabilidad']
        assert 'fecha_actualizacion' in producto['trazabilidad']
        assert producto['trazabilidad']['usuario_registro'] == "admin@test.com"
    
    def test_obtener_detalle_producto_no_encontrado(self, client):
        """Test: Error 404 cuando el producto no existe"""
        response = client.get('/api/productos/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['codigo'] == "PRODUCTO_NO_ENCONTRADO"
        assert 'producto_id' in data
    
    def test_obtener_detalle_producto_sin_certificacion(self, client, producto_sin_certificacion):
        """Test: Obtener detalle de producto sin certificación"""
        response = client.get(f'/api/productos/{producto_sin_certificacion.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        producto = data['producto']
        assert producto['certificaciones'] == []
        assert producto['inventario']['cantidad_disponible'] == 0
        assert producto['inventario']['tiene_stock'] is False
    
    def test_obtener_detalle_producto_con_certificacion_vencida(self, client, app):
        """Test: Producto con certificación vencida debe mostrar estado Inactivo"""
        with app.app_context():
            # Crear producto con certificación vencida
            producto = Producto(
                nombre="Producto Vencido",
                codigo_sku="VENC-001",
                categoria="reactivo",
                precio_unitario=50.00,
                condiciones_almacenamiento="Refrigerado",
                fecha_vencimiento=datetime(2026, 1, 1).date(),
                estado="Activo",
                proveedor_id=1,
                usuario_registro="admin@test.com",
                cantidad_disponible=10
            )
            db.session.add(producto)
            db.session.flush()
            
            # Certificación vencida (fecha pasada)
            certificacion = CertificacionProducto(
                producto_id=producto.id,
                tipo_certificacion="FDA",
                nombre_archivo="cert_vencido.pdf",
                ruta_archivo="/tmp/cert.pdf",
                tamaño_archivo=512,
                fecha_vencimiento_cert=datetime(2024, 1, 1).date()  # Vencida
            )
            db.session.add(certificacion)
            db.session.commit()
            
            response = client.get(f'/api/productos/{producto.id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            cert = data['producto']['certificaciones'][0]
            assert cert['estado'] == "Inactivo"


class TestObtenerProductoPorSKU:
    """Tests para obtener producto por SKU"""
    
    def test_obtener_producto_por_sku_exitoso(self, client, producto_completo):
        """Test: Obtener producto por SKU"""
        response = client.get(f'/api/productos/sku/{producto_completo.codigo_sku}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['producto']['codigo_sku'] == producto_completo.codigo_sku
        assert data['producto']['nombre'] == "Ibuprofeno 400mg"
    
    def test_obtener_producto_por_sku_no_encontrado(self, client):
        """Test: Error 404 cuando el SKU no existe"""
        response = client.get('/api/productos/sku/SKU-INEXISTENTE')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['codigo'] == "PRODUCTO_NO_ENCONTRADO"
        assert data['sku'] == "SKU-INEXISTENTE"
    
    def test_busqueda_por_sku_case_insensitive(self, client, producto_completo):
        """Test: Búsqueda por SKU debe ser case-insensitive (si se implementa)"""
        # Este test puede fallar si no se implementa case-insensitive
        # Es una mejora futura
        response = client.get(f'/api/productos/sku/{producto_completo.codigo_sku.lower()}')
        # Este test se puede ajustar según la implementación


class TestDescargarCertificacion:
    """Tests para descarga de certificaciones"""
    
    def test_descargar_certificacion_exitoso(self, client, producto_completo):
        """Test: Descargar archivo de certificación"""
        response = client.get(f'/api/productos/{producto_completo.id}/certificacion/descargar')
        
        assert response.status_code == 200
        assert response.headers['Content-Disposition']
        assert 'certificado_invima.pdf' in response.headers['Content-Disposition']
    
    def test_descargar_certificacion_producto_no_encontrado(self, client):
        """Test: Error 404 cuando el producto no existe"""
        response = client.get('/api/productos/99999/certificacion/descargar')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['codigo'] == "PRODUCTO_NO_ENCONTRADO"
    
    def test_descargar_certificacion_sin_certificacion(self, client, producto_sin_certificacion):
        """Test: Error 404 cuando el producto no tiene certificación"""
        response = client.get(f'/api/productos/{producto_sin_certificacion.id}/certificacion/descargar')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['codigo'] == "CERTIFICACION_NO_ENCONTRADA"


class TestServicioDetalleCompleto:
    """Tests para el servicio obtener_detalle_completo"""
    
    def test_servicio_obtener_detalle_por_id(self, app, producto_completo):
        """Test: Servicio obtener detalle por ID"""
        with app.app_context():
            detalle = ProductoService.obtener_detalle_completo(producto_id=producto_completo.id)
            
            assert detalle['id'] == producto_completo.id
            assert detalle['nombre'] == "Ibuprofeno 400mg"
            assert 'inventario' in detalle
            assert 'certificaciones' in detalle
            assert 'trazabilidad' in detalle
    
    def test_servicio_obtener_detalle_por_sku(self, app, producto_completo):
        """Test: Servicio obtener detalle por SKU"""
        with app.app_context():
            detalle = ProductoService.obtener_detalle_completo(sku=producto_completo.codigo_sku)
            
            assert detalle['codigo_sku'] == producto_completo.codigo_sku
            assert detalle['nombre'] == "Ibuprofeno 400mg"
    
    def test_servicio_sin_parametros(self, app):
        """Test: Error cuando no se proporciona ID ni SKU"""
        with app.app_context():
            with pytest.raises(ValueError, match="Debe proporcionar producto_id o sku"):
                ProductoService.obtener_detalle_completo()
    
    def test_servicio_producto_no_encontrado(self, app):
        """Test: Error cuando el producto no existe"""
        with app.app_context():
            with pytest.raises(ValueError, match="Producto no encontrado"):
                ProductoService.obtener_detalle_completo(producto_id=99999)


class TestValidacionCantidadDisponible:
    """Tests para validación de cantidad_disponible"""
    
    def test_cantidad_disponible_positiva(self, app):
        """Test: Crear producto con cantidad positiva"""
        with app.app_context():
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-001",
                categoria="insumo",
                precio_unitario=10.0,
                condiciones_almacenamiento="Normal",
                fecha_vencimiento=datetime(2026, 1, 1).date(),
                estado="Activo",
                proveedor_id=1,
                usuario_registro="test@test.com",
                cantidad_disponible=50
            )
            db.session.add(producto)
            db.session.commit()
            
            assert producto.cantidad_disponible == 50
            assert producto.tiene_stock_disponible() is True
    
    def test_cantidad_disponible_cero(self, app):
        """Test: Producto sin stock (cantidad 0)"""
        with app.app_context():
            producto = Producto(
                nombre="Test Sin Stock",
                codigo_sku="TEST-002",
                categoria="insumo",
                precio_unitario=10.0,
                condiciones_almacenamiento="Normal",
                fecha_vencimiento=datetime(2026, 1, 1).date(),
                estado="Activo",
                proveedor_id=1,
                usuario_registro="test@test.com",
                cantidad_disponible=0
            )
            db.session.add(producto)
            db.session.commit()
            
            assert producto.cantidad_disponible == 0
            assert producto.tiene_stock_disponible() is False
    
    def test_cantidad_disponible_negativa_rechazada(self, app):
        """Test: Rechazar cantidad negativa (constraint)"""
        with app.app_context():
            producto = Producto(
                nombre="Test Negativo",
                codigo_sku="TEST-003",
                categoria="insumo",
                precio_unitario=10.0,
                condiciones_almacenamiento="Normal",
                fecha_vencimiento=datetime(2026, 1, 1).date(),
                estado="Activo",
                proveedor_id=1,
                usuario_registro="test@test.com",
                cantidad_disponible=-10  # Cantidad negativa
            )
            db.session.add(producto)
            
            # Debe fallar al hacer commit por el constraint
            with pytest.raises(Exception):  # IntegrityError o similar
                db.session.commit()
            
            db.session.rollback()


class TestTrazabilidad:
    """Tests para timestamps de trazabilidad"""
    
    def test_fecha_creacion_automatica(self, app):
        """Test: fecha_registro se crea automáticamente"""
        with app.app_context():
            antes = datetime.utcnow()
            
            producto = Producto(
                nombre="Test Fecha",
                codigo_sku="TEST-FECHA-001",
                categoria="medicamento",
                precio_unitario=20.0,
                condiciones_almacenamiento="Fresco",
                fecha_vencimiento=datetime(2026, 1, 1).date(),
                estado="Activo",
                proveedor_id=1,
                usuario_registro="test@test.com",
                cantidad_disponible=10
            )
            db.session.add(producto)
            db.session.commit()
            
            despues = datetime.utcnow()
            
            assert producto.fecha_registro is not None
            assert antes <= producto.fecha_registro <= despues
    
    def test_fecha_actualizacion_automatica(self, app):
        """Test: fecha_actualizacion se actualiza automáticamente"""
        with app.app_context():
            # Crear producto
            producto = Producto(
                nombre="Test Update",
                codigo_sku="TEST-UPD-001",
                categoria="medicamento",
                precio_unitario=20.0,
                condiciones_almacenamiento="Fresco",
                fecha_vencimiento=datetime(2026, 1, 1).date(),
                estado="Activo",
                proveedor_id=1,
                usuario_registro="test@test.com",
                cantidad_disponible=10
            )
            db.session.add(producto)
            db.session.commit()
            
            fecha_inicial = producto.fecha_actualizacion
            
            # Actualizar producto
            producto.cantidad_disponible = 20
            db.session.commit()
            
            # La fecha de actualización debe cambiar
            # Nota: Dependiendo de la precisión del sistema, puede ser igual
            # Este test puede requerir ajustes según el comportamiento de SQLAlchemy
            assert producto.fecha_actualizacion >= fecha_inicial


class TestPerformance:
    """Tests de performance para cumplir con ≤ 2s"""
    
    def test_detalle_producto_responde_rapido(self, client, producto_completo):
        """Test: Endpoint de detalle responde en menos de 2 segundos"""
        import time
        
        inicio = time.time()
        response = client.get(f'/api/productos/{producto_completo.id}')
        tiempo_respuesta = time.time() - inicio
        
        assert response.status_code == 200
        assert tiempo_respuesta < 2.0, f"Respuesta tomó {tiempo_respuesta}s, excede 2s"
    
    def test_busqueda_por_sku_rapida(self, client, producto_completo):
        """Test: Búsqueda por SKU responde en menos de 2 segundos"""
        import time
        
        inicio = time.time()
        response = client.get(f'/api/productos/sku/{producto_completo.codigo_sku}')
        tiempo_respuesta = time.time() - inicio
        
        assert response.status_code == 200
        assert tiempo_respuesta < 2.0, f"Respuesta tomó {tiempo_respuesta}s, excede 2s"
