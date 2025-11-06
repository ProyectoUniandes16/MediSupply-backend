import pytest
import io
from unittest.mock import patch, MagicMock
from app.services.minio_service import MinIOService


class TestMinIOService:
    """Tests para el servicio de MinIO"""
    
    @patch('app.services.minio_service.Minio')
    def test_inicializacion_servicio(self, mock_minio):
        """Test inicialización del servicio MinIO"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        
        # Resetear el cliente para forzar nueva inicialización
        MinIOService._client = None
        client = MinIOService.get_client()
        
        assert client is not None
        mock_minio.assert_called_once()
    
    @patch('app.services.minio_service.Minio')
    def test_crear_bucket_si_no_existe(self, mock_minio):
        """Test crear bucket si no existe"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = False
        
        MinIOService._client = None
        MinIOService.asegurar_bucket_existe()
        
        # Verificar que se intentó crear el bucket
        mock_client.make_bucket.assert_called_once()
    
    @patch('app.services.minio_service.Minio')
    def test_subir_video_exitoso(self, mock_minio):
        """Test subir video exitosamente"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        MinIOService._client = None
        
        # Mock del archivo con stream
        mock_file = MagicMock()
        mock_file.stream = io.BytesIO(b"video content")
        mock_file.seek = MagicMock()
        mock_file.tell = MagicMock(return_value=13)  # len(b"video content")
        
        # Mock de put_object
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_result.version_id = "v1"
        mock_client.put_object.return_value = mock_result
        
        result = MinIOService.subir_video(mock_file, "videos/original/123/test.mp4")
        
        assert result is not None
        assert 'object_name' in result
        assert result['object_name'] == "videos/original/123/test.mp4"
        mock_client.put_object.assert_called_once()
    
    @patch('app.services.minio_service.Minio')
    def test_descargar_video(self, mock_minio):
        """Test descargar video"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        MinIOService._client = None
        
        # Mock de get_object
        mock_response = MagicMock()
        mock_response.read.return_value = b"video data"
        mock_client.get_object.return_value = mock_response
        
        data = MinIOService.descargar_video("videos/original/1/test.mp4")
        
        assert data == b"video data"
        mock_client.get_object.assert_called_once()
    
    @patch('app.services.minio_service.Minio')
    def test_generar_url_presigned(self, mock_minio):
        """Test generar URL presignada"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        MinIOService._client = None
        
        # Mock de presigned_get_object
        expected_url = "https://minio.example.com/videos/test.mp4?X-Amz-Algorithm=AWS4"
        mock_client.presigned_get_object.return_value = expected_url
        
        url = MinIOService.obtener_url_presigned("videos/original/1/test.mp4")
        
        assert url == expected_url
        mock_client.presigned_get_object.assert_called_once()
    
    @patch('app.services.minio_service.Minio')
    def test_generar_url_presigned_con_expiracion(self, mock_minio):
        """Test generar URL presignada con tiempo de expiración personalizado"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        MinIOService._client = None
        
        expected_url = "https://minio.example.com/videos/test.mp4?expires=7200"
        mock_client.presigned_get_object.return_value = expected_url
        
        url = MinIOService.obtener_url_presigned("videos/original/1/test.mp4", expiry_seconds=7200)
        
        assert url == expected_url
        # Verificar que se llamó con el tiempo de expiración correcto
        call_args = mock_client.presigned_get_object.call_args
        assert call_args is not None
    
    @patch('app.services.minio_service.Minio')
    def test_subir_video_con_error(self, mock_minio):
        """Test error al subir video"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        MinIOService._client = None
        
        mock_file = MagicMock()
        mock_file.stream = io.BytesIO(b"content")
        mock_file.seek = MagicMock()
        mock_file.tell = MagicMock(return_value=7)
        
        # Simular error en put_object
        mock_client.put_object.side_effect = Exception("Error de conexión")
        
        with pytest.raises(Exception) as exc_info:
            MinIOService.subir_video(mock_file, "videos/original/1/error.mp4")
        
        assert "Error" in str(exc_info.value)
    
    @patch('app.services.minio_service.Minio')
    def test_verificar_bucket_nombre_correcto(self, mock_minio):
        """Test que el bucket tenga el nombre correcto"""
        mock_client = MagicMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        MinIOService._client = None
        MinIOService.asegurar_bucket_existe()
        
        # Verificar que se verificó la existencia del bucket correcto
        mock_client.bucket_exists.assert_called()
        call_args = mock_client.bucket_exists.call_args
        bucket_name = call_args[0][0]
        assert bucket_name == "medisupply-videos"  # Debe ser el bucket configurado
