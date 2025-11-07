"""
Servicio para interactuar con MinIO (almacenamiento de videos)
"""
from minio import Minio
from minio.error import S3Error
from app.config.minio_config import MinIOConfig
from datetime import timedelta
import logging
import io
import os

logger = logging.getLogger(__name__)


class MinIOService:
    """Servicio para gestionar videos en MinIO"""
    
    _client = None
    
    @staticmethod
    def get_client():
        """
        Obtiene o crea el cliente de MinIO
        
        Returns:
            Minio: Cliente de MinIO configurado
        """
        if MinIOService._client is None:
            MinIOService._client = Minio(
                MinIOConfig.MINIO_ENDPOINT,
                access_key=MinIOConfig.MINIO_ACCESS_KEY,
                secret_key=MinIOConfig.MINIO_SECRET_KEY,
                secure=MinIOConfig.MINIO_SECURE
            )
        return MinIOService._client
    
    @staticmethod
    def asegurar_bucket_existe():
        """
        Asegura que el bucket de videos exista, si no lo crea
        
        Returns:
            bool: True si el bucket existe o fue creado exitosamente
        """
        try:
            client = MinIOService.get_client()
            bucket_name = MinIOConfig.MINIO_BUCKET_VIDEOS
            
            if not client.bucket_exists(bucket_name):
                logger.info(f"Creando bucket: {bucket_name}")
                client.make_bucket(bucket_name)
                logger.info(f"Bucket creado exitosamente: {bucket_name}")
            
            return True
        except S3Error as e:
            logger.error(f"Error asegurando bucket: {e}")
            return False
    
    @staticmethod
    def subir_video(file_data, object_name, content_type='video/mp4', metadata=None):
        """
        Sube un video a MinIO
        
        Args:
            file_data: Datos del archivo (FileStorage o bytes)
            object_name: Nombre del objeto en MinIO (ruta completa)
            content_type: Tipo de contenido del video
            metadata: Metadatos adicionales (dict)
            
        Returns:
            dict: Información del archivo subido
            
        Raises:
            Exception: Si falla la subida
        """
        try:
            client = MinIOService.get_client()
            bucket_name = MinIOConfig.MINIO_BUCKET_VIDEOS
            
            # Asegurar que el bucket existe
            MinIOService.asegurar_bucket_existe()
            
            # Si file_data es FileStorage de Flask
            if hasattr(file_data, 'stream'):
                # Obtener el tamaño del archivo
                file_data.seek(0, os.SEEK_END)
                file_size = file_data.tell()
                file_data.seek(0)
                file_stream = file_data.stream
            else:
                # Si es bytes
                file_stream = io.BytesIO(file_data)
                file_size = len(file_data)
            
            # Subir archivo con tamaño conocido
            result = client.put_object(
                bucket_name,
                object_name,
                file_stream,
                length=file_size,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"Video subido exitosamente: {object_name}")
            
            return {
                'bucket': bucket_name,
                'object_name': object_name,
                'etag': result.etag,
                'version_id': result.version_id
            }
            
        except S3Error as e:
            logger.error(f"Error subiendo video a MinIO: {e}")
            raise Exception(f"Error subiendo video: {str(e)}")
    
    @staticmethod
    def obtener_url_presigned(object_name, expiry_seconds=None):
        """
        Genera una URL presigned para reproducir el video
        
        Args:
            object_name: Nombre del objeto en MinIO
            expiry_seconds: Tiempo de expiración en segundos (default: 1 hora)
            
        Returns:
            str: URL presigned
        """
        try:
            client = MinIOService.get_client()
            bucket_name = MinIOConfig.MINIO_BUCKET_VIDEOS
            
            if expiry_seconds is None:
                expiry_seconds = MinIOConfig.PRESIGNED_URL_EXPIRY
            
            # Generar URL presigned
            url = client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expiry_seconds)
            )
            
            logger.info(f"URL presigned generada para: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Error generando URL presigned: {e}")
            raise Exception(f"Error generando URL: {str(e)}")
    
    @staticmethod
    def descargar_video(object_name):
        """
        Descarga un video desde MinIO
        
        Args:
            object_name: Nombre del objeto en MinIO
            
        Returns:
            bytes: Contenido del video
        """
        try:
            client = MinIOService.get_client()
            bucket_name = MinIOConfig.MINIO_BUCKET_VIDEOS
            
            response = client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Video descargado exitosamente: {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error descargando video: {e}")
            raise Exception(f"Error descargando video: {str(e)}")
    
    @staticmethod
    def eliminar_video(object_name):
        """
        Elimina un video de MinIO
        
        Args:
            object_name: Nombre del objeto en MinIO
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            client = MinIOService.get_client()
            bucket_name = MinIOConfig.MINIO_BUCKET_VIDEOS
            
            client.remove_object(bucket_name, object_name)
            logger.info(f"Video eliminado exitosamente: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error eliminando video: {e}")
            return False
    
    @staticmethod
    def verificar_conectividad():
        """
        Verifica la conectividad con MinIO
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            client = MinIOService.get_client()
            # Intentar listar buckets como test de conectividad
            client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"Error de conectividad con MinIO: {e}")
            return False
