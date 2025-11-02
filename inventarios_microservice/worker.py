"""
Worker que se suscribe a Redis Pub/Sub y actualiza el cache.
Versión mejorada con subscripción real.
"""
import requests
import json
import time
import signal
import sys
import logging
import redis
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheWorkerSubscriber:
    """Worker que se suscribe a Redis Pub/Sub y actualiza cache."""
    
    def __init__(self, redis_host: str, redis_port: int, redis_service_url: str, db_connection_string: str):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_service_url = redis_service_url.rstrip('/')
        self.db_connection_string = db_connection_string
        self.running = True
        self.redis_client = None
        self.pubsub = None
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales para shutdown graceful."""
        logger.info(f"⚠️ Señal recibida ({signum}), deteniendo worker...")
        self.running = False
    
    def _connect_redis(self):
        """Conecta a Redis para Pub/Sub."""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"✅ Conectado a Redis: {self.redis_host}:{self.redis_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            return False
    
    def _get_inventarios_from_db(self, producto_id: str) -> list:
        """Consulta inventarios desde la base de datos."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.inventario import Inventario
        
        try:
            engine = create_engine(self.db_connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            inventarios = session.query(Inventario).filter_by(
                producto_id=producto_id
            ).all()
            
            result = [{
                'id': inv.id,
                'productoId': inv.producto_id,
                'cantidad': inv.cantidad,
                'ubicacion': inv.ubicacion,
                'usuarioCreacion': inv.usuario_creacion,
                'fechaCreacion': inv.fecha_creacion.isoformat() if inv.fecha_creacion else None,
                'usuarioActualizacion': inv.usuario_actualizacion,
                'fechaActualizacion': inv.fecha_actualizacion.isoformat() if inv.fecha_actualizacion else None,
            } for inv in inventarios]
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"❌ Error consultando BD: {e}")
            return []
    
    def _update_cache(self, producto_id: str, inventarios: list) -> bool:
        """Actualiza el cache vía Redis Service API."""
        try:
            cache_key = f"inventarios:producto:{producto_id}"
            
            response = requests.post(
                f"{self.redis_service_url}/api/cache/",
                json={
                    'key': cache_key,
                    'value': inventarios,
                    'ttl': 3600
                },
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Cache actualizado: {cache_key} ({len(inventarios)} items)")
                return True
            else:
                logger.error(f"❌ Error actualizando cache: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error actualizando cache: {e}")
            return False

    def _invalidate_aggregate_cache(self):
        """Elimina keys agregadas productos_con_inventarios* para forzar reconstrucción."""
        try:
            pattern = 'productos_con_inventarios*'
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted += self.redis_client.delete(*keys)
                if cursor == 0:
                    break

            if deleted:
                logger.info(f"🗑️  Invalidados {deleted} registros agregados de cache")

        except Exception as e:
            logger.warning(f"⚠️  No se pudieron invalidar caches agregados: {e}")
    
    def _process_message(self, message_data: str):
        """Procesa un mensaje recibido del canal Pub/Sub."""
        try:
            message = json.loads(message_data)
            producto_id = message.get('productoId')
            action = message.get('action')
            
            if not producto_id:
                logger.warning("⚠️ Mensaje sin productoId ignorado")
                return
            
            logger.info(f"📨 Procesando: {action} para producto {producto_id}")
            
            # Recargar inventarios desde BD
            inventarios = self._get_inventarios_from_db(producto_id)
            
            # Actualizar cache
            self._update_cache(producto_id, inventarios)

            # Invalidar cache agregado para reconstrucción en próxima consulta
            self._invalidate_aggregate_cache()
            
            logger.info(f"✅ Procesado: {action} para producto {producto_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando mensaje: {e}")
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
    
    def start(self):
        """Inicia el worker y se suscribe al canal."""
        logger.info("🚀 Iniciando Cache Worker Subscriber...")
        logger.info(f"📡 Redis: {self.redis_host}:{self.redis_port}")
        logger.info(f"🌐 Redis Service API: {self.redis_service_url}")
        logger.info(f"🗄️ Database: {self.db_connection_string.split('@')[1] if '@' in self.db_connection_string else 'local'}")
        
        # Conectar a Redis
        if not self._connect_redis():
            logger.error("❌ No se pudo conectar a Redis. Abortando...")
            sys.exit(1)
        
        # Suscribirse al canal
        try:
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe('inventarios_updates')
            logger.info("✅ Suscrito al canal 'inventarios_updates'")
            logger.info("👂 Escuchando mensajes...")
            
            # Loop de escucha
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'message':
                    self._process_message(message['data'])
                elif message['type'] == 'subscribe':
                    logger.info(f"✅ Subscripción confirmada al canal '{message['channel']}'")
            
        except KeyboardInterrupt:
            logger.info("⚠️ Interrupción de teclado detectada")
        except Exception as e:
            logger.error(f"❌ Error en loop principal: {e}")
        finally:
            if self.pubsub:
                self.pubsub.unsubscribe()
                self.pubsub.close()
            if self.redis_client:
                self.redis_client.close()
            logger.info("🛑 Worker detenido")


def main():
    """Punto de entrada del worker."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_service_url = os.getenv('REDIS_SERVICE_URL', 'http://localhost:5011')
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/inventarios_db')
    
    worker = CacheWorkerSubscriber(redis_host, redis_port, redis_service_url, database_url)
    worker.start()


if __name__ == '__main__':
    main()
