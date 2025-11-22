import pytest
import json
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from app.services.csv_service import CSVProductoService, CSVImportError
from app.models.producto import Producto, CertificacionProducto
from app.extensions import db

class TestCSVProductoServiceCoverage:
    """Tests adicionales para mejorar cobertura de CSVProductoService"""

    def test_procesar_csv_desde_contenido_exitoso_con_inventario(self, app):
        """Test: procesar CSV desde contenido string creando inventarios"""
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id,cantidad,ubicacion
Producto 1,SKU-COV-001,medicamento,10.50,Ambiente,31/12/2025,1,100,Bodega 1
Producto 2,SKU-COV-002,insumo,5.00,Refrigerado,30/06/2026,2,50,Bodega 2"""
        
        with app.app_context():
            # Mock requests.post para inventarios
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 201
                mock_post.return_value = mock_response
                
                # Act
                resultados = CSVProductoService.procesar_csv_desde_contenido(
                    csv_content, 
                    usuario_importacion='test_user'
                )
                
                # Assert
                assert resultados['exitosos'] == 2
                assert resultados['fallidos'] == 0
                
                # Verificar llamadas a inventario
                assert mock_post.call_count == 2
                
                # Verificar payload de la primera llamada
                call_args = mock_post.call_args_list[0]
                url = call_args[0][0]
                kwargs = call_args[1]
                
                assert '/api/inventarios' in url
                assert kwargs['json']['cantidad'] == 100
                assert kwargs['json']['ubicacion'] == 'Bodega 1'
                assert kwargs['json']['usuario'] == 'test_user'

    def test_procesar_csv_desde_contenido_fallo_inventario(self, app):
        """Test: procesar CSV cuando falla la creación de inventario (no debe fallar el producto)"""
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id,cantidad,ubicacion
Producto 1,SKU-COV-003,medicamento,10.50,Ambiente,31/12/2025,1,100,Bodega 1"""
        
        with app.app_context():
            # Mock requests.post para simular error 500
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = "Error interno"
                mock_post.return_value = mock_response
                
                # Act
                resultados = CSVProductoService.procesar_csv_desde_contenido(
                    csv_content, 
                    usuario_importacion='test_user'
                )
                
                # Assert
                assert resultados['exitosos'] == 1
                assert resultados['fallidos'] == 0
                
                # Verificar que el producto sí se creó
                producto = Producto.query.filter_by(codigo_sku='SKU-COV-003').first()
                assert producto is not None

    def test_procesar_csv_desde_contenido_error_conexion_inventario(self, app):
        """Test: procesar CSV cuando hay excepción de conexión con inventario"""
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id,cantidad,ubicacion
Producto 1,SKU-COV-004,medicamento,10.50,Ambiente,31/12/2025,1,100,Bodega 1"""
        
        with app.app_context():
            # Mock requests.post para lanzar excepción
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("Connection refused")
                
                # Act
                resultados = CSVProductoService.procesar_csv_desde_contenido(
                    csv_content, 
                    usuario_importacion='test_user'
                )
                
                # Assert
                assert resultados['exitosos'] == 1
                
                # Verificar que el producto sí se creó
                producto = Producto.query.filter_by(codigo_sku='SKU-COV-004').first()
                assert producto is not None

    def test_procesar_csv_desde_contenido_con_certificacion(self, app):
        """Test: procesar CSV con URL de certificación"""
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id,url_certificacion,tipo_certificacion,fecha_vencimiento_cert
Producto Cert,SKU-CERT-001,medicamento,10.50,Ambiente,31/12/2025,1,http://example.com/cert.pdf,INVIMA,31/12/2026"""
        
        with app.app_context():
            # Act
            resultados = CSVProductoService.procesar_csv_desde_contenido(
                csv_content, 
                usuario_importacion='test_user'
            )
            
            # Assert
            assert resultados['exitosos'] == 1
            
            # Verificar certificación
            producto = Producto.query.filter_by(codigo_sku='SKU-CERT-001').first()
            assert producto.certificacion is not None
            assert producto.certificacion.ruta_archivo == 'http://example.com/cert.pdf'
            assert producto.certificacion.tipo_certificacion == 'INVIMA'

    def test_procesar_csv_desde_contenido_sku_duplicado(self, app):
        """Test: procesar CSV con SKU duplicado"""
        # Crear producto existente
        with app.app_context():
            p = Producto(
                nombre="Existente", codigo_sku="SKU-DUP-EXIST", categoria="medicamento",
                precio_unitario=10, condiciones_almacenamiento="A", fecha_vencimiento=date(2025, 12, 31),
                proveedor_id=1, usuario_registro="test", estado="Activo"
            )
            db.session.add(p)
            db.session.commit()

        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Producto Dup,SKU-DUP-EXIST,medicamento,10.50,Ambiente,31/12/2025,1"""
        
        with app.app_context():
            # Act
            resultados = CSVProductoService.procesar_csv_desde_contenido(csv_content)
            
            # Assert
            assert resultados['exitosos'] == 0
            assert resultados['fallidos'] == 1
            assert resultados['detalles_errores'][0]['codigo'] == 'SKU_DUPLICADO'

    def test_procesar_csv_desde_contenido_error_validacion(self, app):
        """Test: procesar CSV con error de validación (precio inválido)"""
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Producto Malo,SKU-BAD-001,medicamento,INVALIDO,Ambiente,31/12/2025,1"""
        
        with app.app_context():
            # Act
            resultados = CSVProductoService.procesar_csv_desde_contenido(csv_content)
            
            # Assert
            assert resultados['exitosos'] == 0
            assert resultados['fallidos'] == 1
            assert resultados['detalles_errores'][0]['codigo'] == 'PRECIO_INVALIDO'

    def test_procesar_csv_desde_contenido_callback(self, app):
        """Test: verificar que se llama al callback de progreso"""
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
P1,SKU-CB-001,medicamento,10,A,31/12/2025,1
P2,SKU-CB-002,medicamento,10,A,31/12/2025,1"""
        
        mock_callback = Mock()
        
        with app.app_context():
            # Forzar BATCH_SIZE pequeño para asegurar múltiples llamadas si fuera necesario,
            # pero aquí con 2 filas y batch default de 50 solo se llamará una vez al final.
            CSVProductoService.procesar_csv_desde_contenido(
                csv_content, 
                callback_progreso=mock_callback
            )
            
            # Assert
            assert mock_callback.called

    def test_procesar_csv_desde_contenido_csv_vacio(self, app):
        """Test: procesar CSV vacío lanza excepción"""
        with app.app_context():
            with pytest.raises(CSVImportError) as exc:
                CSVProductoService.procesar_csv_desde_contenido("")
            assert exc.value.args[0]['codigo'] == 'CSV_VACIO'

    def test_procesar_csv_desde_contenido_columnas_faltantes(self, app):
        """Test: procesar CSV con columnas faltantes"""
        csv_content = "nombre,codigo_sku"
        with app.app_context():
            with pytest.raises(CSVImportError) as exc:
                CSVProductoService.procesar_csv_desde_contenido(csv_content)
            assert exc.value.args[0]['codigo'] == 'COLUMNAS_FALTANTES'
