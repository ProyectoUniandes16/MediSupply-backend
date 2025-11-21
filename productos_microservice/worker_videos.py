"""
Worker para procesamiento de videos en paralelo con multithreading
Procesa videos usando ffmpeg para generar versiones optimizadas para PC y mobile
Usa Redis Pub/Sub para recibir mensajes de videos a procesar
"""
import os
import sys
import json
import logging
import subprocess
import threading
import redis
import signal
from queue import Queue
from datetime import datetime

# Agregar path para importar módulos de la app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.video_evidencia import VideoEvidencia
from app.services.minio_service import MinIOService
from app.extensions import db
from app import create_app

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Número de workers en paralelo
NUM_WORKERS = 3


class VideoProcessor:
    """Clase para procesar videos individualmente"""
    
    @staticmethod
    def procesar_video_ffmpeg(input_path, output_path, preset='pc'):
        """
        Procesa un video con ffmpeg
        
        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida
            preset: Tipo de preset ('pc' o 'mobile')
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            # Configuración según preset
            if preset == 'mobile':
                # Móvil: menor resolución, menor bitrate
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-vf', 'scale=720:-2',  # 720p, mantener aspect ratio
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '28',  # Mayor compresión
                    '-c:a', 'aac',
                    '-b:a', '96k',
                    '-movflags', '+faststart',
                    '-y',  # Sobrescribir si existe
                    output_path
                ]
            else:  # pc
                # PC: mayor calidad
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-vf', 'scale=1920:-2',  # 1080p, mantener aspect ratio
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',  # Mejor calidad
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-movflags', '+faststart',
                    '-y',
                    output_path
                ]
            
            # Ejecutar ffmpeg
            logger.info(f"Procesando video {preset}: {input_path}")
            
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600  # 10 minutos max
            )
            
            if result.returncode == 0:
                logger.info(f"Video procesado exitosamente ({preset}): {output_path}")
                return True
            else:
                logger.error(f"Error en ffmpeg ({preset}): {result.stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout procesando video ({preset})")
            return False
        except Exception as e:
            logger.error(f"Error procesando video ({preset}): {e}")
            return False
    
    @staticmethod
    def procesar_video_completo(video_id, ruta_original):
        """
        Procesa un video completo: descarga, procesa y sube versiones
        
        Args:
            video_id: ID del video en la base de datos
            ruta_original: Ruta del video original en MinIO
            
        Returns:
            dict: Resultado del procesamiento
        """
        app = create_app()
        
        with app.app_context():
            try:
                # 1. Obtener registro del video
                video = VideoEvidencia.query.get(video_id)
                if not video:
                    logger.error(f"Video {video_id} no encontrado en DB")
                    return {'success': False, 'error': 'Video no encontrado'}
                
                # 2. Marcar como procesando
                video.marcar_como_procesando()
                db.session.commit()
                logger.info(f"Video {video_id} marcado como procesando")
                
                # 3. Crear directorio temporal
                temp_dir = '/tmp/video_processing' if os.name != 'nt' else 'C:\\temp\\video_processing'
                os.makedirs(temp_dir, exist_ok=True)
                
                # 4. Descargar video original desde MinIO
                temp_input = os.path.join(temp_dir, f"input_{video_id}.{video.formato_original}")
                logger.info(f"Descargando video desde MinIO: {ruta_original}")
                
                video_data = MinIOService.descargar_video(ruta_original)
                
                with open(temp_input, 'wb') as f:
                    f.write(video_data)
                
                logger.info(f"Video descargado: {temp_input}")
                
                # 5. Procesar para PC
                temp_output_pc = os.path.join(temp_dir, f"output_pc_{video_id}.mp4")
                success_pc = VideoProcessor.procesar_video_ffmpeg(
                    temp_input, temp_output_pc, preset='pc'
                )
                
                if not success_pc:
                    raise Exception("Error procesando versión PC")
                
                # 6. Procesar para mobile
                temp_output_mobile = os.path.join(temp_dir, f"output_mobile_{video_id}.mp4")
                success_mobile = VideoProcessor.procesar_video_ffmpeg(
                    temp_input, temp_output_mobile, preset='mobile'
                )
                
                if not success_mobile:
                    raise Exception("Error procesando versión mobile")
                
                # 7. Subir versiones procesadas a MinIO
                producto_id = video.producto_id
                base_name = os.path.splitext(video.nombre_archivo_minio)[0]
                
                # Subir versión PC
                ruta_pc = f"videos/procesado/{producto_id}/{base_name}_procesado_pc.mp4"
                with open(temp_output_pc, 'rb') as f:
                    MinIOService.subir_video(
                        file_data=f.read(),
                        object_name=ruta_pc,
                        content_type='video/mp4',
                        metadata={'preset': 'pc', 'video_id': str(video_id)}
                    )
                
                logger.info(f"Versión PC subida: {ruta_pc}")
                
                # Subir versión mobile
                ruta_mobile = f"videos/procesado/{producto_id}/{base_name}_procesado_mobile.mp4"
                with open(temp_output_mobile, 'rb') as f:
                    MinIOService.subir_video(
                        file_data=f.read(),
                        object_name=ruta_mobile,
                        content_type='video/mp4',
                        metadata={'preset': 'mobile', 'video_id': str(video_id)}
                    )
                
                logger.info(f"Versión mobile subida: {ruta_mobile}")
                
                # 8. Actualizar registro en DB
                video.marcar_como_procesado(ruta_pc=ruta_pc, ruta_mobile=ruta_mobile)
                db.session.commit()
                
                logger.info(f"Video {video_id} procesado exitosamente")
                
                # 9. Limpiar archivos temporales
                try:
                    os.remove(temp_input)
                    os.remove(temp_output_pc)
                    os.remove(temp_output_mobile)
                except:
                    pass
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'ruta_pc': ruta_pc,
                    'ruta_mobile': ruta_mobile
                }
                
            except Exception as e:
                logger.error(f"Error procesando video {video_id}: {e}", exc_info=True)
                
                # Marcar video como error
                try:
                    video = VideoEvidencia.query.get(video_id)
                    if video:
                        video.marcar_error(str(e))
                        db.session.commit()
                except:
                    pass
                
                return {'success': False, 'error': str(e)}


def worker_thread(worker_id, task_queue):
    """
    Thread worker que procesa videos de la cola
    
    Args:
        worker_id: ID del worker
        task_queue: Cola de tareas
    """
    logger.info(f"Worker {worker_id} iniciado")
    
    while True:
        try:
            # Obtener tarea de la cola
            task = task_queue.get()
            
            if task is None:
                # Señal de parada
                logger.info(f"Worker {worker_id} detenido")
                break
            
            video_id = task['video_id']
            ruta_original = task['ruta_video']
            
            logger.info(f"Worker {worker_id} procesando video {video_id}")
            
            # Procesar video
            result = VideoProcessor.procesar_video_completo(video_id, ruta_original)
            
            if result['success']:
                logger.info(f"Worker {worker_id} completó video {video_id}")
            else:
                logger.error(f"Worker {worker_id} falló procesando video {video_id}: {result.get('error')}")
            
            # Marcar tarea como completada
            task_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error en worker {worker_id}: {e}", exc_info=True)
            task_queue.task_done()


def callback_mensaje_redis(message_data: str, task_queue: Queue):
    """
    Callback para procesar mensajes de Redis Pub/Sub
    
    Args:
        message_data: Cuerpo del mensaje (JSON string)
        task_queue: Cola de tareas para los workers
    """
    try:
        mensaje = json.loads(message_data)
        
        video_id = mensaje.get('video_id')
        estado = mensaje.get('estado')
        ruta_video = mensaje.get('ruta_video')
        
        logger.info(f"📨 Mensaje recibido - Video: {video_id}, Estado: {estado}")
        
        # Solo procesar si está en estado 'cargado'
        if estado == 'cargado':
            # Agregar a cola de procesamiento
            task_queue.put({
                'video_id': video_id,
                'ruta_video': ruta_video,
                'metadata': mensaje.get('metadata', {})
            })
            
            logger.info(f"✅ Video {video_id} agregado a cola de procesamiento")
        else:
            logger.info(f"⏭️ Video {video_id} ignorado (estado: {estado})")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error decodificando mensaje: {e}")
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Iniciando worker de procesamiento de videos")
    logger.info(f"Workers en paralelo: {NUM_WORKERS}")
    logger.info("=" * 60)
    
    # Crear aplicación Flask (para contexto de DB)
    app = create_app()
    
    # Crear cola de tareas para workers
    task_queue = Queue()
    
    # Crear y arrancar workers
    workers = []
    for i in range(NUM_WORKERS):
        worker = threading.Thread(
            target=worker_thread,
            args=(i + 1, task_queue),
            daemon=True
        )
        worker.start()
        workers.append(worker)
    
    logger.info(f"✅ {NUM_WORKERS} workers iniciados correctamente")
    
    # Configuración de Redis - soporta varias formas de pasar la configuración
    # - REDIS_URL (ej: redis://host:6379/0)
    # - REDIS_PORT puede venir como un número o como 'tcp://ip:port'
    # - REDIS_HOST, REDIS_DB
    def _parse_redis_env():
        """Devuelve (host, port, db) leyendo varias formas de variables de entorno."""
        from urllib.parse import urlparse
        import re

        # 1) REDIS_URL (prioritario)
        redis_url = os.getenv('REDIS_URL') or os.getenv('REDIS_URI') or os.getenv('REDIS')
        if redis_url:
            try:
                parsed = urlparse(redis_url)
                host = parsed.hostname or os.getenv('REDIS_HOST', 'localhost')
                port = parsed.port or int(os.getenv('REDIS_PORT', 6379))
                # path puede ser '/0' -> extraer número de DB
                db = 0
                if parsed.path and parsed.path.lstrip('/'):
                    try:
                        db = int(parsed.path.lstrip('/'))
                    except Exception:
                        db = int(os.getenv('REDIS_DB', 0))
                else:
                    db = int(os.getenv('REDIS_DB', 0))
                return host, int(port), int(db)
            except Exception:
                # Si falla el parseo, seguir a las siguientes opciones
                pass

        # 2) REDIS_PORT puede ser un entero o algo como 'tcp://10.100.134.245:6379'
        redis_port_env = os.getenv('REDIS_PORT')
        redis_host_env = os.getenv('REDIS_HOST')
        if redis_port_env:
            # Buscar host:port dentro del valor
            m = re.search(r'(?:(?:[a-z]+:\/\/)?(?P<host>[^:\/]+):)?(?P<port>\d{2,5})', redis_port_env)
            if m:
                host = m.group('host') or redis_host_env or os.getenv('REDIS_HOST', 'localhost')
                try:
                    port = int(m.group('port'))
                except Exception:
                    port = int(os.getenv('REDIS_PORT', 6379)) if os.getenv('REDIS_PORT', '').isdigit() else 6379
                db = int(os.getenv('REDIS_DB', 0))
                return host, port, db

        # 3) Fallback: valores individuales o por defecto
        host = redis_host_env or os.getenv('REDIS_HOST', 'localhost')
        try:
            port = int(os.getenv('REDIS_PORT', 6379))
        except Exception:
            port = 6379
        try:
            db = int(os.getenv('REDIS_DB', 0))
        except Exception:
            db = 0
        return host, port, db

    redis_host, redis_port, redis_db = _parse_redis_env()
    logger.info(f"📡 Conectando a Redis: {redis_host}:{redis_port} (db={redis_db})")
    
    # Variables de control
    redis_client = None
    pubsub = None
    running = [True]  # Usar lista para poder modificar en signal_handler
    
    def signal_handler(signum, frame):
        """Maneja señales para shutdown graceful."""
        logger.info(f"⚠️ Señal recibida ({signum}), deteniendo worker...")
        running[0] = False
    
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Conectar a Redis
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=5
        )

        # Test de conexión
        redis_client.ping()
        logger.info("✅ Conectado a Redis exitosamente")

        # Suscribirse al canal de procesamiento de videos
        pubsub = redis_client.pubsub()
        pubsub.subscribe('video_processing')
        logger.info("✅ Suscrito al canal 'video_processing'")
        logger.info("👂 Esperando mensajes...")

        # Loop de escucha
        for message in pubsub.listen():
            if not running[0]:
                logger.info("🛑 Deteniendo loop de escucha...")
                break

            if message['type'] == 'message':
                callback_mensaje_redis(message['data'], task_queue)
            elif message['type'] == 'subscribe':
                logger.info(f"✅ Subscripción confirmada al canal '{message['channel']}'")
        
    except redis.ConnectionError as e:
        logger.error(f"❌ Error de conexión a Redis: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción de teclado detectada")
    except Exception as e:
        logger.error(f"❌ Error fatal en worker: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        logger.info("🧹 Limpiando recursos...")
        
        # Detener workers
        logger.info("⏹️ Deteniendo workers de procesamiento...")
        for _ in range(NUM_WORKERS):
            task_queue.put(None)
        
        for worker in workers:
            worker.join(timeout=5)
        
        # Cerrar Redis
        if pubsub:
            pubsub.unsubscribe()
            pubsub.close()
        if redis_client:
            redis_client.close()
        
        logger.info("✅ Worker detenido correctamente")
