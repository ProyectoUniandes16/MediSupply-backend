"""
Servicio para encolar mensajes en Redis Queue.
"""
import requests
import logging
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class RedisQueueService:
    """Cliente para encolar mensajes en Redis Service."""
    
    @staticmethod
    def _get_redis_url() -> str:
        """Obtiene la URL del Redis Service desde la configuración."""
        return current_app.config.get('REDIS_SERVICE_URL', 'http://localhost:5011').rstrip('/')
    
    @staticmethod
    def enqueue_cache_update(producto_id: str, action: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Encola un mensaje para actualizar el cache de inventarios.
        
        Args:
            producto_id: ID del producto
            action: create, update, delete, adjust
            data: Datos adicionales opcionales
        
        Returns:
            True si se encoló correctamente, False si hubo error
        """
        try:
            redis_url = RedisQueueService._get_redis_url()
            
            message = {
                'productoId': producto_id,
                'action': action,
                'data': data or {}
            }
            
            payload = {
                'channel': 'inventarios_updates',
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
                logger.info(f"✅ Mensaje encolado: {action} para producto {producto_id} ({subscribers} workers)")
                return True
            else:
                logger.error(f"❌ Error encolando mensaje: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"⚠️ Redis Service no disponible: {e}")
            # No fallar la operación si Redis no está disponible
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado encolando mensaje: {e}")
            return False
    
    @staticmethod
    def check_health() -> bool:
        """Verifica que Redis Service esté disponible."""
        try:
            redis_url = RedisQueueService._get_redis_url()
            response = requests.get(f"{redis_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
