"""
Configuración de MinIO para almacenamiento de videos
"""
import os
import logging

logger = logging.getLogger(__name__)


class MinIOConfig:
    """Configuración centralizada de MinIO"""
    
    # MinIO Connection
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'  # HTTP o HTTPS
    
    # Buckets
    MINIO_BUCKET_VIDEOS = os.getenv('MINIO_BUCKET_VIDEOS', 'medisupply-videos')
    
    # Configuración de videos
    MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150 MB en bytes
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
    
    # URLs presigned
    PRESIGNED_URL_EXPIRY = int(os.getenv('PRESIGNED_URL_EXPIRY', 3600))  # 1 hora por defecto
    
    # Feature flags
    USE_MINIO = os.getenv('USE_MINIO', 'true').lower() == 'true'
    
    @staticmethod
    def verificar_configuracion():
        """
        Verifica que la configuración de MinIO sea válida
        
        Returns:
            dict: Estado de la configuración
        """
        estado = {
            'minio_configurado': False,
            'disponible': False,
            'errores': []
        }
        
        if not MinIOConfig.USE_MINIO:
            estado['errores'].append('MinIO deshabilitado (USE_MINIO=false)')
            return estado
        
        # Verificar configuración básica
        if not MinIOConfig.MINIO_ENDPOINT:
            estado['errores'].append('MINIO_ENDPOINT no configurado')
            return estado
        
        if not MinIOConfig.MINIO_ACCESS_KEY or not MinIOConfig.MINIO_SECRET_KEY:
            estado['errores'].append('Credenciales MinIO no configuradas')
            return estado
        
        estado['minio_configurado'] = True
        
        return estado
