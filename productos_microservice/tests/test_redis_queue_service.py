import requests
import pytest
from unittest.mock import patch, MagicMock
from app.services.redis_queue_service import RedisQueueService


class TestRedisQueueService:
    """Tests para el servicio de cola Redis"""
    
    def test_obtener_redis_url(self):
        """Test obtener URL del servicio Redis"""
        import os
        # El método es privado y estático
        url = RedisQueueService._get_redis_url()
        assert url is not None
        assert isinstance(url, str)
    
    @patch('requests.post')
    def test_publicar_cambio_estado_exitoso(self, mock_post):
        """Test publicar cambio de estado exitosamente"""
        # Mock de respuesta exitosa
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"subscribers": 1}
        mock_post.return_value = mock_response
        
        result = RedisQueueService.publicar_mensaje_video(
            video_id=1,
            producto_id=10,
            estado='cargado',
            ruta_video='videos/original/10/test.mp4'
        )
        
        # Verificar que se llamó a requests.post
        assert mock_post.called
        assert result == True
        
        # Verificar los argumentos de la llamada
        call_args = mock_post.call_args
        assert 'publish' in call_args[0][0]  # URL debe contener 'publish'
    
    @patch('requests.post')
    def test_publicar_cambio_estado_con_datos_completos(self, mock_post):
        """Test publicar con todos los datos del video"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"subscribers": 1}
        mock_post.return_value = mock_response
        
        metadata = {
            'nombre_archivo': 'producto_demo.mp4',
            'usuario_creacion': 'admin@test.com',
            'fecha_creacion': '2024-01-15T10:30:00'
        }
        
        result = RedisQueueService.publicar_mensaje_video(
            video_id=5,
            producto_id=100,
            estado='procesando',
            ruta_video='videos/original/100/producto_demo.mp4',
            metadata=metadata
        )
        
        # Verificar que se envió correctamente
        assert result == True
        call_args = mock_post.call_args
        assert call_args[1]['json']['channel'] == 'video_processing'
        assert 'message' in call_args[1]['json']
    
    @patch('requests.post')
    def test_publicar_cambio_estado_diferentes_estados(self, mock_post):
        """Test publicar diferentes estados de video"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"subscribers": 1}
        mock_post.return_value = mock_response
        
        estados = ['cargando', 'cargado', 'procesando', 'procesado']
        
        for estado in estados:
            RedisQueueService.publicar_mensaje_video(
                video_id=1,
                producto_id=1,
                estado=estado,
                ruta_video='videos/original/1/test.mp4'
            )
        
        # Verificar que se llamó 4 veces (una por cada estado)
        assert mock_post.call_count == 4
    
    @patch('requests.post')
    def test_publicar_cambio_estado_error_conexion(self, mock_post):
        """Test error de conexión al publicar"""
        # Simular error de conexión
        mock_post.side_effect = requests.RequestException("Error de conexión")
        
        # No debe lanzar excepción, debe retornar False
        result = RedisQueueService.publicar_mensaje_video(
            video_id=1,
            producto_id=1,
            estado='cargado',
            ruta_video='videos/original/1/test.mp4'
        )
        
        assert result == False

    @patch('requests.get')
    def test_verificar_conectividad_exitoso(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert RedisQueueService.verificar_conectividad() is True

    @patch('requests.get')
    def test_verificar_conectividad_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("down")

        assert RedisQueueService.verificar_conectividad() is False
    
    @patch('requests.post')
    def test_publicar_cambio_estado_respuesta_error(self, mock_post):
        """Test respuesta de error del servidor Redis"""
        # Mock de respuesta con error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error interno del servidor"
        mock_post.return_value = mock_response
        
        # Debe retornar False
        result = RedisQueueService.publicar_mensaje_video(
            video_id=1,
            producto_id=1,
            estado='cargado',
            ruta_video='videos/original/1/test.mp4'
        )
        
        assert result == False
    
    @patch('requests.post')
    def test_canal_correcto(self, mock_post):
        """Test que se usa el canal correcto"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"subscribers": 1}
        mock_post.return_value = mock_response
        
        RedisQueueService.publicar_mensaje_video(
            video_id=1,
            producto_id=1,
            estado='cargado',
            ruta_video='videos/original/1/test.mp4'
        )
        
        # Verificar que el canal es 'video_processing'
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['channel'] == 'video_processing'
    
    @patch('requests.post')
    def test_formato_mensaje_json(self, mock_post):
        """Test que el mensaje se envía en formato JSON correcto"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"subscribers": 1}
        mock_post.return_value = mock_response
        
        metadata = {
            'ruta_pc': 'videos/procesado/99/video_pc.mp4',
            'ruta_mobile': 'videos/procesado/99/video_mobile.mp4'
        }
        
        RedisQueueService.publicar_mensaje_video(
            video_id=42,
            producto_id=99,
            estado='procesado',
            ruta_video='videos/original/99/video.mp4',
            metadata=metadata
        )
        
        # Verificar estructura del JSON
        call_args = mock_post.call_args
        assert 'json' in call_args[1]
        payload = call_args[1]['json']
        assert 'channel' in payload
        assert 'message' in payload
        
        # Verificar que el mensaje contiene los datos del video
        mensaje = payload['message']
        assert mensaje['video_id'] == 42
        assert mensaje['estado'] == 'procesado'
