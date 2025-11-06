"""
Servicio para publicar mensajes en Redis Pub/Sub para procesamiento de videos.
Usa el Redis Service existente.
"""
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RedisQueueService:
    """Cliente para publicar mensajes de videos en Redis Pub/Sub."""
    
    @staticmethod
    def _get_redis_url() -> str:
        """Obtiene la URL del Redis Service desde variables de entorno."""
        import os
        return os.getenv('REDIS_SERVICE_URL', 'http://localhost:5011').rstrip('/')
    
    @staticmethod
    def publicar_mensaje_video(video_id: int, producto_id: int, estado: str, ruta_video: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publica un mensaje para procesamiento de video.
        
        Args:
            video_id: ID del video en la base de datos
            producto_id: ID del producto asociado
            estado: Estado del video (cargado, procesando, procesado)
            ruta_video: Ruta del video en MinIO
            metadata: Metadatos adicionales opcionales
        
        Returns:
            True si se publicó correctamente, False si hubo error
        """
        try:
            redis_url = RedisQueueService._get_redis_url()
            
            message = {
                'video_id': video_id,
                'producto_id': producto_id,
                'estado': estado,
                'ruta_video': ruta_video,
                'metadata': metadata or {}
            }
            
            payload = {
                'channel': 'video_processing',
                'message': message
            }
            
            response = requests.post(
                f"{redis_url}/api/queue/publish",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                subscribers = result.get('subscribers', 0)
                logger.info(f"✅ Mensaje publicado: video {video_id} - Estado: {estado} ({subscribers} workers escuchando)")
                return True
            else:
                logger.error(f"❌ Error publicando mensaje: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"⚠️ Redis Service no disponible: {e}")
            # No fallar la operación si Redis no está disponible
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado publicando mensaje: {e}")
            return False
    
    @staticmethod
    def verificar_conectividad() -> bool:
        """
        Verifica que Redis Service esté disponible.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            redis_url = RedisQueueService._get_redis_url()
            response = requests.get(f"{redis_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
