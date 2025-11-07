"""
Blueprint para gestión de videos de productos
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.models.video_evidencia import VideoEvidencia
from app.models.producto import Producto
from app.services.minio_service import MinIOService
from app.services.redis_queue_service import RedisQueueService
from app.config.minio_config import MinIOConfig
from app.extensions import db
from datetime import datetime
import os
import uuid
import logging

logger = logging.getLogger(__name__)

videos_bp = Blueprint('videos', __name__, url_prefix='/api/productos')


def validar_extension_video(filename):
    """
    Valida que el archivo tenga una extensión permitida
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        bool: True si la extensión es válida
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in MinIOConfig.ALLOWED_VIDEO_EXTENSIONS


def validar_tamaño_video(file_size):
    """
    Valida que el archivo no exceda el tamaño máximo
    
    Args:
        file_size: Tamaño del archivo en bytes
        
    Returns:
        bool: True si el tamaño es válido
    """
    return file_size <= MinIOConfig.MAX_VIDEO_SIZE


def generar_nombre_unico_video(filename, producto_id):
    """
    Genera un nombre único para el video en MinIO
    
    Args:
        filename: Nombre original del archivo
        producto_id: ID del producto
        
    Returns:
        str: Nombre único del archivo
    """
    extension = filename.rsplit('.', 1)[1].lower()
    unique_id = uuid.uuid4().hex[:12]
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{producto_id}_{timestamp}_{unique_id}.{extension}"


@videos_bp.route('/<int:producto_id>/videos', methods=['POST'])
def subir_video(producto_id):
    """
    Endpoint para subir un video de evidencia para un producto
    
    Validaciones:
    - Formato: MP4, MOV, AVI
    - Tamaño máximo: 150 MB
    - Descripción obligatoria
    
    Args:
        producto_id: ID del producto
        
    Form-data esperado:
        - video: Archivo de video
        - descripcion: Descripción del video (obligatorio)
        - usuario_registro: Usuario que sube el video
        
    Returns:
        201: Video subido exitosamente
        400: Datos inválidos
        404: Producto no encontrado
        413: Archivo muy grande
        500: Error interno
    """
    try:
        # 1. Verificar que el producto existe
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({
                "error": "Producto no encontrado",
                "codigo": "PRODUCTO_NO_ENCONTRADO",
                "producto_id": producto_id
            }), 404
        
        # 2. Validar que se envió un archivo
        if 'video' not in request.files:
            return jsonify({
                "error": "No se proporcionó ningún archivo de video",
                "codigo": "ARCHIVO_FALTANTE",
                "campo_esperado": "video"
            }), 400
        
        archivo_video = request.files['video']
        
        # 3. Validar nombre de archivo
        if not archivo_video.filename or archivo_video.filename == '':
            return jsonify({
                "error": "El archivo no tiene nombre",
                "codigo": "ARCHIVO_INVALIDO"
            }), 400
        
        # 4. Validar formato
        if not validar_extension_video(archivo_video.filename):
            return jsonify({
                "error": "El formato del archivo no es válido.",
                "codigo": "FORMATO_INVALIDO",
                "formatos_permitidos": list(MinIOConfig.ALLOWED_VIDEO_EXTENSIONS)
            }), 400
        
        # 5. Validar tamaño del archivo
        archivo_video.seek(0, os.SEEK_END)
        file_size = archivo_video.tell()
        archivo_video.seek(0)
        
        if not validar_tamaño_video(file_size):
            max_mb = MinIOConfig.MAX_VIDEO_SIZE / (1024 * 1024)
            return jsonify({
                "error": "El archivo supera el tamaño máximo permitido.",
                "codigo": "ARCHIVO_MUY_GRANDE",
                "tamaño_archivo_mb": round(file_size / (1024 * 1024), 2),
                "tamaño_maximo_mb": int(max_mb)
            }), 413
        
        # 6. Validar descripción
        descripcion = request.form.get('descripcion', '').strip()
        if not descripcion:
            return jsonify({
                "error": "La descripción del video es obligatoria",
                "codigo": "DESCRIPCION_FALTANTE"
            }), 400
        
        # 7. Obtener usuario
        usuario_registro = request.form.get('usuario_registro', 'sistema')
        
        # 8. Generar nombre único para el video
        nombre_original = secure_filename(archivo_video.filename)
        extension = nombre_original.rsplit('.', 1)[1].lower()
        nombre_archivo_minio = generar_nombre_unico_video(nombre_original, producto_id)
        
        # 9. Definir ruta en MinIO
        ruta_original = f"videos/original/{producto_id}/{nombre_archivo_minio}"
        
        # 10. Crear registro en DB (estado: cargando)
        video_evidencia = VideoEvidencia(
            producto_id=producto_id,
            nombre_original=nombre_original,
            nombre_archivo_minio=nombre_archivo_minio,
            tamaño_archivo=file_size,
            formato_original=extension,
            descripcion=descripcion,
            estado='cargando',
            ruta_original=ruta_original,
            usuario_registro=usuario_registro
        )
        
        db.session.add(video_evidencia)
        db.session.commit()
        
        video_id = video_evidencia.id
        
        # 11. Subir video a MinIO
        try:
            archivo_video.seek(0)  # Reset stream
            
            metadata = {
                'video_id': str(video_id),
                'producto_id': str(producto_id),
                'usuario': usuario_registro,
                'descripcion': descripcion[:200]  # Limitar metadatos
            }
            
            MinIOService.subir_video(
                file_data=archivo_video,
                object_name=ruta_original,
                content_type=f'video/{extension}',
                metadata=metadata
            )
            
            logger.info(f"Video {video_id} subido a MinIO: {ruta_original}")
            
        except Exception as e:
            logger.error(f"Error subiendo video a MinIO: {str(e)}")
            # Marcar video como error en DB
            video_evidencia.marcar_error(f"Error subiendo a MinIO: {str(e)}")
            db.session.commit()
            
            return jsonify({
                "error": "No fue posible subir el video. Intenta nuevamente.",
                "codigo": "ERROR_SUBIDA_MINIO",
                "detalles": str(e)
            }), 500
        
        # 12. Actualizar estado a 'cargado'
        video_evidencia.marcar_como_cargado()
        db.session.commit()
        
        # 13. Publicar mensaje a Redis Pub/Sub para procesamiento
        try:
            metadata_msg = {
                'nombre_original': nombre_original,
                'tamaño_bytes': file_size,
                'formato': extension,
                'usuario': usuario_registro
            }
            
            RedisQueueService.publicar_mensaje_video(
                video_id=video_id,
                producto_id=producto_id,
                estado='cargado',
                ruta_video=ruta_original,
                metadata=metadata_msg
            )
            
            logger.info(f"Mensaje publicado a Redis para video {video_id}")
            
        except Exception as e:
            logger.error(f"Error publicando mensaje a Redis: {str(e)}")
            # No fallar la request, el video está subido
            # El worker puede procesar manualmente si es necesario
        
        # 14. Preparar respuesta exitosa
        respuesta = {
            "mensaje": "Video agregado exitosamente.",
            "estado": "confirmado",
            "video": {
                "id": video_id,
                "producto_id": producto_id,
                "nombre_original": nombre_original,
                "tamaño_mb": round(file_size / (1024 * 1024), 2),
                "formato": extension,
                "descripcion": descripcion,
                "estado": video_evidencia.estado,
                "fecha_subida": video_evidencia.fecha_subida.strftime("%Y-%m-%d %H:%M:%S"),
                "usuario_registro": usuario_registro
            },
            "procesamiento": {
                "estado": "en_cola",
                "mensaje": "El video está en cola para ser procesado"
            }
        }
        
        return jsonify(respuesta), 201
        
    except Exception as e:
        logger.error(f"Error inesperado subiendo video: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            "error": "No fue posible subir el video. Intenta nuevamente.",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500


@videos_bp.route('/<int:producto_id>/videos', methods=['GET'])
def listar_videos_producto(producto_id):
    """
    Endpoint para listar todos los videos de un producto
    
    Args:
        producto_id: ID del producto
        
    Returns:
        200: Lista de videos
        404: Producto no encontrado
        500: Error interno
    """
    try:
        # Verificar que el producto existe
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({
                "error": "Producto no encontrado",
                "codigo": "PRODUCTO_NO_ENCONTRADO",
                "producto_id": producto_id
            }), 404
        
        # Obtener videos del producto
        videos = VideoEvidencia.query.filter_by(producto_id=producto_id).order_by(
            VideoEvidencia.fecha_subida.desc()
        ).all()
        
        # Serializar videos
        videos_data = []
        for video in videos:
            video_dict = video.to_dict()
            
            # Si está procesado, generar URL presigned
            if video.esta_procesado() and video.ruta_procesado_pc:
                try:
                    url = MinIOService.obtener_url_presigned(video.ruta_procesado_pc)
                    video_dict['url_reproduccion'] = url
                except Exception as e:
                    logger.error(f"Error generando URL para video {video.id}: {e}")
                    video_dict['url_reproduccion'] = None
            
            videos_data.append(video_dict)
        
        respuesta = {
            "producto_id": producto_id,
            "total_videos": len(videos_data),
            "videos": videos_data
        }
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        logger.error(f"Error listando videos: {str(e)}")
        return jsonify({
            "error": "Error obteniendo videos del producto",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500


@videos_bp.route('/videos/<int:video_id>', methods=['GET'])
def obtener_video(video_id):
    """
    Endpoint para obtener detalles de un video específico
    
    Args:
        video_id: ID del video
        
    Returns:
        200: Detalles del video con URL de reproducción
        404: Video no encontrado
        500: Error interno
    """
    try:
        video = VideoEvidencia.query.get(video_id)
        
        if not video:
            return jsonify({
                "error": "Video no encontrado",
                "codigo": "VIDEO_NO_ENCONTRADO",
                "video_id": video_id
            }), 404
        
        video_dict = video.to_dict()
        
        # Si está procesado, generar URL presigned
        if video.esta_procesado() and video.ruta_procesado_pc:
            try:
                url_pc = MinIOService.obtener_url_presigned(video.ruta_procesado_pc)
                url_mobile = MinIOService.obtener_url_presigned(video.ruta_procesado_mobile) if video.ruta_procesado_mobile else None
                
                video_dict['urls_reproduccion'] = {
                    'pc': url_pc,
                    'mobile': url_mobile,
                    'expira_en_segundos': MinIOConfig.PRESIGNED_URL_EXPIRY
                }
            except Exception as e:
                logger.error(f"Error generando URLs para video {video_id}: {e}")
                video_dict['urls_reproduccion'] = None
        
        return jsonify({"video": video_dict}), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo video: {str(e)}")
        return jsonify({
            "error": "Error obteniendo video",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500


@videos_bp.route('/videos/<int:video_id>/status', methods=['GET'])
def obtener_status_video(video_id):
    """
    Endpoint para obtener el estado de procesamiento de un video
    
    Args:
        video_id: ID del video
        
    Returns:
        200: Estado del video
        404: Video no encontrado
        500: Error interno
    """
    try:
        video = VideoEvidencia.query.get(video_id)
        
        if not video:
            return jsonify({
                "error": "Video no encontrado",
                "codigo": "VIDEO_NO_ENCONTRADO",
                "video_id": video_id
            }), 404
        
        # Determinar mensaje según estado
        mensajes = {
            'cargando': 'El video está siendo cargado',
            'cargado': 'El video está en cola para procesamiento',
            'procesando': 'El video está siendo procesado',
            'procesado': 'El video ha sido procesado exitosamente',
            'error': 'Ocurrió un error procesando el video'
        }
        
        respuesta = {
            "video_id": video_id,
            "estado": video.estado,
            "mensaje": mensajes.get(video.estado, 'Estado desconocido'),
            "fecha_subida": video.fecha_subida.strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_procesado": video.fecha_procesado.strftime("%Y-%m-%d %H:%M:%S") if video.fecha_procesado else None,
            "disponible_para_reproduccion": video.esta_procesado()
        }
        
        if video.estado == 'error':
            respuesta['error_detalle'] = video.mensaje_error
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo status de video: {str(e)}")
        return jsonify({
            "error": "Error obteniendo estado del video",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500
