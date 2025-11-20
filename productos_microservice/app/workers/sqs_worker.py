"""Worker para procesar importaciones masivas usando Redis"""
import os
import sys
import signal
import logging
import json
from typing import Optional

import redis

# Añadir el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.extensions import db
from app.models.import_job import ImportJob
from app.services.csv_service import CSVProductoService, CSVImportError
from app.services.local_import_service import LocalImportService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable global para manejo de shutdown graceful
shutdown_requested = False
REDIS_CHANNEL = os.getenv('REDIS_IMPORT_CHANNEL', 'productos_import_csv')


def signal_handler(signum, frame):
    """Maneja señales de terminación (SIGTERM, SIGINT)"""
    global shutdown_requested
    logger.info(f"Señal {signum} recibida. Iniciando shutdown graceful...")
    shutdown_requested = True


def _parse_message_data(data) -> Optional[dict]:
    """Convierte el payload recibido desde Redis a dict"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        if isinstance(data, str):
            return json.loads(data)
        if isinstance(data, dict):
            return data
        logger.error("❌ Formato de mensaje no soportado")
        return None
    except json.JSONDecodeError as exc:
        logger.error(f"❌ Mensaje con JSON inválido: {exc}")
        return None


def procesar_mensaje(app, payload: dict) -> bool:
    """Procesa un mensaje publicado en el canal Redis"""
    job_id = payload.get('job_id')
    local_path = payload.get('local_path')
    usuario_registro = payload.get('usuario_registro', 'sistema')
    metadata = payload.get('metadata', {})

    if not job_id:
        logger.error("❌ Mensaje inválido: falta job_id")
        return False

    try:
        with app.app_context():
            job = db.session.query(ImportJob).filter_by(id=job_id).first()

            if not job:
                logger.error(f"❌ Job {job_id} no encontrado en la base de datos")
                return False

            if metadata.get('total_filas') and not job.total_filas:
                job.total_filas = metadata['total_filas']

            ruta_archivo = job.local_path or local_path
            if not ruta_archivo:
                error_msg = "Ruta del archivo local no registrada"
                logger.error(error_msg)
                job.marcar_como_fallido(error_msg)
                db.session.commit()
                return False

            if not os.path.exists(ruta_archivo):
                error_msg = f"Archivo CSV no encontrado en disco: {ruta_archivo}"
                logger.error(error_msg)
                job.marcar_como_fallido(error_msg)
                db.session.commit()
                return False

            job.marcar_como_procesando()
            db.session.commit()
            logger.info(f"🔄 Job {job_id} marcado como PROCESANDO")

            try:
                contenido_csv = LocalImportService.leer_csv(ruta_archivo)
            except Exception as e:
                error_msg = f"No se pudo leer el CSV local: {e}"
                logger.error(error_msg)
                job.marcar_como_fallido(error_msg)
                db.session.commit()
                return False

            def actualizar_progreso(fila_actual: int, total_filas: int, exitosos: int, fallidos: int):
                try:
                    job.filas_procesadas = fila_actual
                    job.exitosos = exitosos
                    job.fallidos = fallidos
                    if total_filas > 0:
                        job.progreso = round((fila_actual / total_filas) * 100, 2)
                    else:
                        job.progreso = 0
                    db.session.commit()
                except Exception as e:
                    logger.error(f"❌ Error actualizando progreso del job {job_id}: {e}")
                    db.session.rollback()

            logger.info(f"🚀 Procesando CSV local: {ruta_archivo}")
            csv_service = CSVProductoService()
            resultado = csv_service.procesar_csv_desde_contenido(
                contenido_csv=contenido_csv,
                usuario_importacion=usuario_registro,
                callback_progreso=actualizar_progreso
            )

            exitosos = resultado.get('exitosos', 0)
            fallidos = resultado.get('fallidos', 0)
            detalles_errores = resultado.get('detalles_errores', [])
            total_procesados = exitosos + fallidos

            job.actualizar_progreso(
                filas_procesadas=total_procesados,
                exitosos=exitosos,
                fallidos=fallidos
            )

            if detalles_errores:
                errores_limitados = detalles_errores[:100]
                job.detalles_errores = {
                    'total_errores': fallidos,
                    'errores_capturados': len(errores_limitados),
                    'nota': 'Mostrando primeros 100 errores' if fallidos > 100 else 'Todos los errores capturados',
                    'errores': errores_limitados
                }

            job.marcar_como_completado(
                mensaje=f"{exitosos} exitosos, {fallidos} fallidos"
            )
            db.session.commit()

            logger.info(f"✅ Job {job_id} COMPLETADO: {exitosos} exitosos, {fallidos} fallidos")
            return True

    except CSVImportError as e:
        logger.error(f"❌ Error de validación CSV para job {job_id}: {e.args[0]}")
        with app.app_context():
            job = db.session.query(ImportJob).filter_by(id=job_id).first()
            if job:
                job.marcar_como_fallido(json.dumps(e.args[0]))
                db.session.commit()
        return False
    except Exception as e:
        logger.error(f"❌ Error procesando job {job_id}: {e}", exc_info=True)
        with app.app_context():
            job = db.session.query(ImportJob).filter_by(id=job_id).first()
            if job:
                job.marcar_como_fallido(f"Error en worker: {e}")
                db.session.commit()
        return False


def run_worker():
    """Worker principal que escucha el canal Redis y procesa mensajes"""
    logger.info("=" * 80)
    logger.info("🚀 Iniciando Redis Worker para importación de productos")
    logger.info("=" * 80)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    app = create_app()

    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_db = int(os.getenv('REDIS_DB', 0))
    redis_password = os.getenv('REDIS_PASSWORD')

    redis_client = None
    pubsub = None

    mensajes_procesados = 0
    mensajes_exitosos = 0
    mensajes_fallidos = 0

    try:
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False,
            socket_connect_timeout=5,
            health_check_interval=30
        )
        redis_client.ping()
        logger.info(f"✅ Conectado a Redis {redis_host}:{redis_port} (db {redis_db})")

        pubsub = redis_client.pubsub()
        pubsub.subscribe(REDIS_CHANNEL)
        logger.info(f"👂 Escuchando canal '{REDIS_CHANNEL}'")

        for message in pubsub.listen():
            if shutdown_requested:
                logger.info("🛑 Shutdown solicitado, deteniendo worker")
                break

            if message['type'] != 'message':
                continue

            payload = _parse_message_data(message['data'])
            if not payload:
                mensajes_fallidos += 1
                continue

            mensajes_procesados += 1
            logger.info(f"📥 Mensaje recibido para job {payload.get('job_id')}")

            exito = procesar_mensaje(app, payload)
            if exito:
                mensajes_exitosos += 1
            else:
                mensajes_fallidos += 1

            logger.info(
                "📊 Stats -> Procesados: %s | Exitosos: %s | Fallidos: %s",
                mensajes_procesados,
                mensajes_exitosos,
                mensajes_fallidos
            )

    except redis.ConnectionError as e:
        logger.error(f"❌ Error de conexión a Redis: {e}")
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupción manual recibida")
    except Exception as e:
        logger.error(f"❌ Error fatal en worker: {e}", exc_info=True)
    finally:
        logger.info("🧹 Limpiando recursos...")
        if pubsub:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except Exception:
                pass
        if redis_client:
            redis_client.close()

        logger.info("🛑 Worker detenido")
        logger.info(f"📊 Estadísticas finales:")
        logger.info(f"   - Mensajes procesados: {mensajes_procesados}")
        logger.info(f"   - Exitosos: {mensajes_exitosos}")
        logger.info(f"   - Fallidos: {mensajes_fallidos}")
        logger.info("=" * 80)


if __name__ == '__main__':
    run_worker()
