"""
Worker que escucha la cola de Redis y actualiza el cache.
"""
import requests
import json
import time
import signal
import sys
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheWorker:
    """Worker que procesa mensajes de la cola y actualiza el cache."""
    
    def __init__(self, redis_service_url: str, db_connection_string: str):
        self.redis_service_url = redis_service_url.rstrip('/')
        self.db_connection_string = db_connection_string
        self.running = True
        
        # Configurar manejo de señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de sistema para shutdown graceful."""
        logger.info(f"⚠️ Señal recibida ({signum}), deteniendo worker...")
        self.running = False
    
    def _get_inventarios_from_db(self, producto_id: str) -> list:
        """
        Consulta todos los inventarios de un producto desde la base de datos.
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Lista de inventarios del producto
        """
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
        """
        Actualiza el cache con los inventarios de un producto.
        
        Args:
            producto_id: ID del producto
            inventarios: Lista de inventarios a guardar
        
        Returns:
            True si se actualizó correctamente
        """
        try:
            cache_key = f"inventarios:producto:{producto_id}"
            
            response = requests.post(
                f"{self.redis_service_url}/api/cache/",
                json={
                    'key': cache_key,
                    'value': inventarios,
                    'ttl': 3600  # 1 hora
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
    
    def _process_message(self, message: Dict[str, Any]):
        """
        Procesa un mensaje de la cola.
        
        Args:
            message: Mensaje recibido con estructura {productoId, action, data}
        """
        try:
            producto_id = message.get('productoId')
            action = message.get('action')
            
            if not producto_id:
                logger.warning("⚠️ Mensaje sin productoId ignorado")
                return
            
            logger.info(f"📨 Procesando: {action} para producto {producto_id}")
            
            # Para cualquier acción, recargamos todos los inventarios del producto desde la BD
            inventarios = self._get_inventarios_from_db(producto_id)
            
            # Actualizar cache
            self._update_cache(producto_id, inventarios)
            
            logger.info(f"✅ Procesado: {action} para producto {producto_id}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
    
    def start(self):
        """Inicia el worker y comienza a procesar mensajes."""
        logger.info("🚀 Iniciando Cache Worker...")
        logger.info(f"📡 Redis Service: {self.redis_service_url}")
        logger.info(f"🗄️ Database: {self.db_connection_string.split('@')[1] if '@' in self.db_connection_string else 'local'}")
        
        # Verificar conexión a Redis Service
        try:
            response = requests.get(f"{self.redis_service_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Conexión a Redis Service OK")
            else:
                logger.warning(f"⚠️ Redis Service responde con status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ No se puede conectar a Redis Service: {e}")
            sys.exit(1)
        
        logger.info("👂 Escuchando cola 'inventarios_updates'...")
        
        # Polling de la cola (simplificado - en producción usar un verdadero subscriber)
        while self.running:
            try:
                # Verificar si hay canales activos
                response = requests.get(
                    f"{self.redis_service_url}/api/queue/channels?pattern=inventarios_updates",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    channels = data.get('channels', [])
                    
                    if channels:
                        logger.debug(f"Canal activo con {channels[0].get('subscribers', 0)} subscriptores")
                
                # En esta implementación simplificada, el worker espera eventos
                # En producción, usarías redis-py para subscribe real
                time.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("⚠️ Interrupción de teclado detectada")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop principal: {e}")
                time.sleep(5)
        
        logger.info("🛑 Worker detenido")


def main():
    """Punto de entrada del worker."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    redis_service_url = os.getenv('REDIS_SERVICE_URL', 'http://localhost:5011')
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/inventarios_db')
    
    worker = CacheWorker(redis_service_url, database_url)
    worker.start()


if __name__ == '__main__':
    main()
