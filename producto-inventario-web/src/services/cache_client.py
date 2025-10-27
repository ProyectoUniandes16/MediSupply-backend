"""
Cliente para consultar cache de inventarios desde Redis Service.
"""
import requests
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class CacheClient:
    """Cliente para leer cache de inventarios (READ-ONLY)."""
    
    def __init__(self, redis_service_url: str):
        self.redis_service_url = redis_service_url.rstrip('/')
        self.cache_endpoint = f"{self.redis_service_url}/api/cache"
    
    def get_inventarios_by_producto(self, producto_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene inventarios de un producto desde el cache.
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Lista de inventarios o None si no está en cache
        """
        try:
            cache_key = f"inventarios:producto:{producto_id}"
            
            response = requests.get(
                f"{self.cache_endpoint}/{cache_key}",
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                inventarios = data.get('value', [])
                logger.info(f"✅ Cache HIT: {cache_key} ({len(inventarios)} items)")
                return inventarios
            elif response.status_code == 404:
                logger.info(f"⚠️ Cache MISS: {cache_key}")
                return None
            else:
                logger.error(f"❌ Error consultando cache: {response.status_code}")
                return None
                
        except requests.Timeout:
            logger.warning(f"⏱️ Timeout consultando cache para producto {producto_id}")
            return None
        except requests.RequestException as e:
            logger.error(f"❌ Error de conexión con Redis Service: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado consultando cache: {e}")
            return None
    
    def is_available(self) -> bool:
        """Verifica que Redis Service esté disponible."""
        try:
            response = requests.get(f"{self.redis_service_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
