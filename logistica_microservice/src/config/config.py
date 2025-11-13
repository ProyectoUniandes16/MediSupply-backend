import os
from datetime import timedelta

class Config:
    """
    Configuración del microservicio de logística
    """
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Configuración del servidor
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5013))
    
    # Configuración de base de datos PostgreSQL (usa BD común del proyecto)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'medisupply')
    DB_USER = os.environ.get('DB_USER', 'medisupply_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'medisupply_password')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = False  # Token no expira
    
    # Configuración de OpenRouteService API
    ORS_API_KEY = os.environ.get('ORS_API_KEY', 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQ5M2RlMmQzNDkzOTRjZGU4ZWYyY2YxZmRhYTlhZDBlIiwiaCI6Im11cm11cjY0In0=')
