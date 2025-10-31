import os

class Config:
    """
    Configuración del BFF mediador-movil
    """
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Configuración del servidor
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5004))
    
    # Configuración de microservicios
    AUTH_URL = os.environ.get('AUTH_URL', 'http://localhost:5001')
    CLIENTES_URL = os.environ.get('CLIENTES_URL', 'http://localhost:5010')
    VENDEDORES_URL = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    PEDIDOS_URL = os.environ.get('PEDIDOS_URL', 'http://localhost:5011')
    
    # Configuración de JWT (debe coincidir con auth-usuario)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
