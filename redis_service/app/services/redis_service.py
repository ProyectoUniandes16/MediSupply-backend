"""
Servicio de Redis para Cache y Cola (Pub/Sub)
"""
import json
import redis
from typing import Optional, Dict, Any, List
from datetime import timedelta


class RedisService:
    """Servicio para manejar operaciones de Redis"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pubsub = None
        self.config = None
    
    def init_app(self, app):
        """Inicializar Redis con la configuración de Flask"""
        self.config = app.config
        
        try:
            self.client = redis.Redis(
                host=app.config['REDIS_HOST'],
                port=app.config['REDIS_PORT'],
                db=app.config['REDIS_DB'],
                password=app.config['REDIS_PASSWORD'],
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Test conexión
            self.client.ping()
            app.logger.info(f"✅ Redis conectado en {app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}")
            
        except redis.ConnectionError as e:
            app.logger.error(f"❌ Error conectando a Redis: {e}")
            raise
    
    def is_available(self) -> bool:
        """Verificar si Redis está disponible"""
        try:
            return self.client.ping() if self.client else False
        except:
            return False
    
    # ============================================
    # OPERACIONES DE CACHE
    # ============================================
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            raise Exception(f"Error al obtener cache: {str(e)}")
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Guardar valor en cache
        
        Args:
            key: Clave del cache
            value: Valor a guardar (será serializado a JSON)
            ttl: Tiempo de vida en segundos (None = usa default)
        """
        try:
            ttl = ttl or self.config['CACHE_DEFAULT_TTL']
            serialized = json.dumps(value)
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            raise Exception(f"Error al guardar en cache: {str(e)}")
    
    def cache_delete(self, key: str) -> int:
        """Eliminar clave del cache"""
        try:
            return self.client.delete(key)
        except Exception as e:
            raise Exception(f"Error al eliminar cache: {str(e)}")
    
    def cache_delete_pattern(self, pattern: str) -> int:
        """
        Eliminar múltiples claves que coincidan con un patrón
        
        Args:
            pattern: Patrón Redis (ej: "inventarios:producto:*")
        
        Returns:
            Número de claves eliminadas
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            raise Exception(f"Error al eliminar claves por patrón: {str(e)}")
    
    def cache_exists(self, key: str) -> bool:
        """Verificar si una clave existe en cache"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            raise Exception(f"Error al verificar existencia: {str(e)}")
    
    def cache_ttl(self, key: str) -> int:
        """Obtener tiempo de vida restante de una clave (en segundos)"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            raise Exception(f"Error al obtener TTL: {str(e)}")
    
    def cache_keys(self, pattern: str = "*") -> List[str]:
        """Listar claves que coincidan con un patrón"""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            raise Exception(f"Error al listar claves: {str(e)}")
    
    def cache_flush(self) -> bool:
        """Limpiar todo el cache (¡usar con precaución!)"""
        try:
            return self.client.flushdb()
        except Exception as e:
            raise Exception(f"Error al limpiar cache: {str(e)}")
    
    # ============================================
    # OPERACIONES DE COLA (PUB/SUB)
    # ============================================
    
    def queue_publish(self, channel: str, message: Dict[str, Any]) -> int:
        """
        Publicar mensaje en un canal
        
        Args:
            channel: Nombre del canal
            message: Mensaje a publicar (será serializado a JSON)
        
        Returns:
            Número de subscriptores que recibieron el mensaje
        """
        try:
            serialized = json.dumps(message)
            return self.client.publish(channel, serialized)
        except Exception as e:
            raise Exception(f"Error al publicar mensaje: {str(e)}")
    
    def queue_subscribe(self, channels: List[str]):
        """
        Suscribirse a uno o más canales
        
        Args:
            channels: Lista de nombres de canales
        
        Returns:
            Objeto PubSub para escuchar mensajes
        """
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            raise Exception(f"Error al suscribirse: {str(e)}")
    
    def queue_channels(self, pattern: str = "*") -> List[str]:
        """Listar canales activos que coincidan con un patrón"""
        try:
            return self.client.pubsub_channels(pattern)
        except Exception as e:
            raise Exception(f"Error al listar canales: {str(e)}")
    
    def queue_num_subscribers(self, channel: str) -> int:
        """Obtener número de subscriptores en un canal"""
        try:
            result = self.client.pubsub_numsub(channel)
            return result[0][1] if result else 0
        except Exception as e:
            raise Exception(f"Error al obtener subscriptores: {str(e)}")
    
    # ============================================
    # ESTADÍSTICAS Y MONITOREO
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servidor Redis"""
        try:
            info = self.client.info()
            return {
                'redis_version': info.get('redis_version'),
                'uptime_in_seconds': info.get('uptime_in_seconds'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace': info.get(f'db{self.config["REDIS_DB"]}', {}),
                'pubsub_channels': len(self.client.pubsub_channels()),
                'status': 'connected'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# Instancia global
redis_client = RedisService()
