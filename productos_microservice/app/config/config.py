import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///productos.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta")
    
    # Configuración para upload de archivos
    MAX_CONTENT_LENGTH = 150 * 1024 * 1024  # 150MB máximo por archivo (videos)
    
    # Usar ruta absoluta para evitar problemas con directorio de trabajo
    # Si la app se ejecuta desde run.py, el cwd será productos_microservice/
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads'))
    
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # Configuración de seguridad
    SEND_FILE_MAX_AGE_DEFAULT = 300  # Cache de archivos por 5 minutos

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
