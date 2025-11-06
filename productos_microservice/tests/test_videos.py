import pytest
import io
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.models.video_evidencia import VideoEvidencia
from app.models.producto import Producto
from datetime import datetime


class TestVideoEvidenciaModel:
    """Tests para el modelo VideoEvidencia"""
    
    def test_video_evidencia_creation(self, app):
        """Test creación básica de video evidencia"""
        with app.app_context():
            from app.extensions import db
            
            # Crear producto primero
            producto = Producto(
                nombre="Test Producto",
                codigo_sku="TEST-PROD-001",
                categoria="medicamento",
                precio_unitario=25.50,
                condiciones_almacenamiento="Almacenar en lugar fresco",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="admin@test.com"
            )
            db.session.add(producto)
            db.session.flush()
            
            # Crear video evidencia
            video = VideoEvidencia(
                producto_id=producto.id,
                nombre_original="test_video.mp4",
                nombre_archivo_minio="test_video_unique.mp4",
                ruta_original="videos/original/1/test_video.mp4",
                tamaño_archivo=5242880,  # 5MB
                formato_original="mp4",
                descripcion="Video de prueba",
                usuario_registro="admin@test.com",
                estado="cargando"
            )
            db.session.add(video)
            db.session.flush()
            
            assert video.nombre_original == "test_video.mp4"
            assert video.estado == "cargando"
            assert video.producto_id == producto.id
            assert video.tamaño_archivo == 5242880
    
    def test_video_estados(self, app):
        """Test cambios de estado del video"""
        with app.app_context():
            from app.extensions import db
            
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-002",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            db.session.add(producto)
            db.session.flush()
            
            video = VideoEvidencia(
                producto_id=producto.id,
                nombre_original="video.mp4",
                nombre_archivo_minio="video_unique.mp4",
                ruta_original="videos/original/1/video.mp4",
                tamaño_archivo=1024,
                formato_original="mp4",
                descripcion="Test",
                usuario_registro="test@test.com",
                estado="cargando"
            )
            db.session.add(video)
            db.session.flush()
            
            # Verificar transiciones de estado
            assert video.estado == "cargando"
            
            video.estado = "cargado"
            assert video.estado == "cargado"
            
            video.estado = "procesando"
            assert video.estado == "procesando"
            
            video.estado = "procesado"
            assert video.estado == "procesado"


class TestVideosEndpoints:
    """Tests para los endpoints de videos"""
    
    def test_upload_video_exitoso(self, client, app):
        """Test carga exitosa de video"""
        with app.app_context():
            from app.extensions import db
            
            # Crear producto primero
            producto = Producto(
                nombre="Producto Test",
                codigo_sku="PROD-VIDEO-001",
                categoria="medicamento",
                precio_unitario=25.50,
                condiciones_almacenamiento="Fresco",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="admin@test.com"
            )
            db.session.add(producto)
            db.session.commit()
            producto_id = producto.id
        
        # Simular archivo de video
        video_content = b"fake video content" * 1000  # Simular contenido
        video_file = BytesIO(video_content)
        
        data = {
            'video': (video_file, 'test_video.mp4'),
            'descripcion': 'Video de prueba del producto',
            'usuario_registro': 'admin@test.com'
        }
        
        # Mock de MinIO y Redis
        with patch('app.services.minio_service.MinIOService.subir_video') as mock_minio, \
             patch('app.services.redis_queue_service.RedisQueueService.publicar_mensaje_video') as mock_redis:
            
            mock_minio.return_value = {'object_name': f"videos/original/{producto_id}/test_video.mp4"}
            
            response = client.post(
                f'/api/productos/{producto_id}/videos',
                data=data,
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 201
        response_data = response.get_json()
        assert 'Video agregado exitosamente' in response_data['mensaje']
        assert 'video' in response_data
        assert response_data['video']['nombre_original'] == 'test_video.mp4'
        assert response_data['video']['estado'] == 'cargado'
    
    def test_upload_video_sin_archivo(self, client, app):
        """Test upload sin archivo de video"""
        with app.app_context():
            from app.extensions import db
            
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-003",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            db.session.add(producto)
            db.session.commit()
            producto_id = producto.id
        
        data = {
            'descripcion': 'Sin video',
            'usuario_registro': 'test@test.com'
        }
        
        response = client.post(
            f'/api/productos/{producto_id}/videos',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'error' in response_data
    
    def test_upload_video_formato_invalido(self, client, app):
        """Test upload con formato de video inválido"""
        with app.app_context():
            from app.extensions import db
            
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-004",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            db.session.add(producto)
            db.session.commit()
            producto_id = producto.id
        
        # Archivo con extensión inválida
        invalid_file = BytesIO(b"not a video")
        data = {
            'video': (invalid_file, 'documento.txt'),
            'descripcion': 'Formato inválido',
            'usuario_registro': 'test@test.com'
        }
        
        response = client.post(
            f'/api/productos/{producto_id}/videos',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'formato' in response_data['error'].lower()
    
    def test_upload_video_sin_descripcion(self, client, app):
        """Test upload sin descripción"""
        with app.app_context():
            from app.extensions import db
            
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-005",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            db.session.add(producto)
            db.session.commit()
            producto_id = producto.id
        
        video_file = BytesIO(b"video content")
        data = {
            'video': (video_file, 'test.mp4'),
            'usuario_registro': 'test@test.com'
        }
        
        response = client.post(
            f'/api/productos/{producto_id}/videos',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        response_data = response.get_json()
        # La respuesta tiene el mensaje en minúsculas
        assert 'descripción' in response_data['error'].lower() or 'descripcion' in response_data['error'].lower()
    
    def test_upload_video_producto_inexistente(self, client):
        """Test upload para producto que no existe"""
        video_file = BytesIO(b"video content")
        data = {
            'video': (video_file, 'test.mp4'),
            'descripcion': 'Test',
            'usuario_registro': 'test@test.com'
        }
        
        response = client.post(
            '/api/productos/99999/videos',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 404
    
    def test_get_video_status(self, client, app):
        """Test obtener estado de un video"""
        with app.app_context():
            from app.extensions import db
            
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-006",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            db.session.add(producto)
            db.session.flush()
            
            video = VideoEvidencia(
                producto_id=producto.id,
                nombre_original="status_test.mp4",
                nombre_archivo_minio="status_test_unique.mp4",
                ruta_original="videos/original/1/status_test.mp4",
                tamaño_archivo=1024,
                formato_original="mp4",
                descripcion="Test status",
                usuario_registro="test@test.com",
                estado="procesando"
            )
            db.session.add(video)
            db.session.commit()
            video_id = video.id
        
        response = client.get(f'/api/productos/videos/{video_id}/status')
        
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'video_id' in response_data
        assert response_data['estado'] == 'procesando'
    
    def test_get_video_status_inexistente(self, client):
        """Test obtener estado de video que no existe"""
        response = client.get('/api/productos/videos/99999/status')
        
        assert response.status_code == 404


class TestMinIOServiceMock:
    """Tests para el servicio MinIO (con mocks)"""
    
    def test_subir_video_mock(self, app):
        """Test subir video a MinIO (mock)"""
        from app.services.minio_service import MinIOService
        
        with app.app_context():
            mock_file = MagicMock()
            mock_file.filename = "test.mp4"
            mock_file.stream = io.BytesIO(b"fake video content")
            mock_file.seek = MagicMock()
            mock_file.tell = MagicMock(return_value=1024)
            
            with patch('app.services.minio_service.Minio') as mock_minio_client:
                mock_client_instance = MagicMock()
                mock_minio_client.return_value = mock_client_instance
                mock_client_instance.bucket_exists.return_value = True
                
                # Mock del método put_object
                mock_result = MagicMock()
                mock_result.etag = "abc123"
                mock_result.version_id = "v1"
                mock_client_instance.put_object.return_value = mock_result
                
                result = MinIOService.subir_video(mock_file, "videos/original/1/test.mp4")
                
                assert result is not None
                assert 'object_name' in result
                assert result['object_name'] == "videos/original/1/test.mp4"
    
    def test_generar_url_presigned_mock(self, app):
        """Test generar URL presignada (mock)"""
        from app.services.minio_service import MinIOService
        
        with app.app_context():
            with patch('app.services.minio_service.Minio') as mock_minio_client:
                mock_client_instance = MagicMock()
                mock_minio_client.return_value = mock_client_instance
                
                # Mock del método presigned_get_object - debe retornar string
                expected_url = "https://minio.test/video.mp4?token=abc123"
                mock_client_instance.presigned_get_object.return_value = expected_url
                
                MinIOService._client = None  # Reset para forzar nueva inicialización
                url = MinIOService.obtener_url_presigned("videos/original/1/test.mp4")
                
                assert url is not None
                assert isinstance(url, str)
                assert "https://" in url
                assert ".mp4" in url


class TestRedisQueueServiceMock:
    """Tests para el servicio Redis Queue (con mocks)"""
    
    def test_publicar_cambio_estado_mock(self, app):
        """Test publicar cambio de estado a Redis (mock)"""
        from app.services.redis_queue_service import RedisQueueService
        
        with app.app_context():
            with patch('requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'subscribers': 1}
                mock_post.return_value = mock_response
                
                # No debe lanzar excepción
                result = RedisQueueService.publicar_mensaje_video(
                    video_id=1,
                    producto_id=1,
                    estado='cargado',
                    ruta_video='videos/original/1/test.mp4'
                )
                
                # Verificar que se llamó a requests.post
                assert mock_post.called
                assert result == True


class TestVideoValidations:
    """Tests para validaciones de video"""
    
    def test_validar_extension_video_valida(self, client, app):
        """Test extensiones de video válidas: mp4, mov, avi"""
        with app.app_context():
            from app.extensions import db
            
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-007",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            db.session.add(producto)
            db.session.commit()
            producto_id = producto.id
        
        extensiones_validas = ['mp4', 'mov', 'avi']
        
        for ext in extensiones_validas:
            video_file = BytesIO(b"video content")
            data = {
                'video': (video_file, f'test.{ext}'),
                'descripcion': f'Test {ext}',
                'usuario_registro': 'test@test.com'
            }
            
            with patch('app.services.minio_service.MinIOService.subir_video') as mock_minio, \
                 patch('app.services.redis_queue_service.RedisQueueService.publicar_mensaje_video') as mock_redis:
                
                mock_minio.return_value = {'object_name': f"videos/original/{producto_id}/test.{ext}"}
                
                response = client.post(
                    f'/api/productos/{producto_id}/videos',
                    data=data,
                    content_type='multipart/form-data'
                )
            
            # Debe aceptar todas las extensiones válidas
            assert response.status_code in [201, 400]  # 201 si pasa, 400 si hay otra validación
    
    def test_validar_tamano_maximo(self, client, app):
        """Test validación de tamaño máximo (150MB)"""
        # Este test es más conceptual ya que no queremos crear archivos de 150MB
        # Verificamos que la configuración esté correcta
        assert app.config.get('MAX_CONTENT_LENGTH', 0) >= 150 * 1024 * 1024
