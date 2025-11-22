"""
Servicio para guardar y leer archivos CSV localmente en local_imports/
"""
import os
import shutil
from datetime import datetime
import uuid

class LocalImportService:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'local_imports'))

    @staticmethod
    def guardar_csv(archivo, usuario_registro):
        """
        Guarda un archivo CSV en local_imports/
        Args:
            archivo: FileStorage o file-like object
            usuario_registro: usuario
        Returns:
            tuple: (local_path, nombre_archivo)
        """
        if not os.path.exists(LocalImportService.BASE_DIR):
            os.makedirs(LocalImportService.BASE_DIR)

        # Nombre seguro y único
        nombre_archivo = getattr(archivo, 'filename', getattr(archivo, 'name', 'unknown.csv'))
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        nombre_seguro = nombre_archivo.replace(' ', '_').replace('/', '_')
        local_path = os.path.join(LocalImportService.BASE_DIR, f"{usuario_registro}_{timestamp}_{unique_id}_{nombre_seguro}")

        # Guardar archivo
        if hasattr(archivo, 'stream'):
            archivo.stream.seek(0)
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(archivo.stream, f)
        else:
            archivo.seek(0)
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(archivo, f)

        return local_path, nombre_archivo

    @staticmethod
    def leer_csv(local_path):
        """
        Lee el contenido de un archivo CSV local con múltiples intentos de encoding
        """
        try:
            # Intento 1: UTF-8 con BOM (estándar moderno)
            with open(local_path, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Intento 2: Latin-1 (común en Excel Windows en español)
                with open(local_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                # Intento 3: UTF-8 ignorando errores (último recurso)
                with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
