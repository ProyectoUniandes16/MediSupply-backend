"""
Servicio para publicar y consumir mensajes de importación masiva de productos usando Redis
"""
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RedisImportQueueService:
    DEFAULT_CHANNEL = 'productos_import_csv'

    @staticmethod
    def _get_redis_url() -> str:
        import os
        return os.getenv('REDIS_SERVICE_URL', 'http://localhost:5011').rstrip('/')

    @staticmethod
    @staticmethod
    def _get_channel() -> str:
        import os
        return os.getenv('REDIS_IMPORT_CHANNEL', RedisImportQueueService.DEFAULT_CHANNEL)

    @staticmethod
    def publicar_import_job(job_id: str, local_path: str, nombre_archivo: str, usuario_registro: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publica un mensaje de importación masiva en Redis
        """
        try:
            redis_url = RedisImportQueueService._get_redis_url()
            message = {
                'job_id': job_id,
                'local_path': local_path,
                'nombre_archivo': nombre_archivo,
                'usuario_registro': usuario_registro,
                'metadata': metadata or {}
            }
            payload = {
                'channel': RedisImportQueueService._get_channel(),
                'message': message
            }
            response = requests.post(f"{redis_url}/api/queue/publish", json=payload, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Job {job_id} publicado en Redis import queue")
                return True
            else:
                logger.error(f"❌ Error publicando job en Redis: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error inesperado publicando job en Redis: {e}")
            return False
