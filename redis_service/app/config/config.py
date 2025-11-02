"""
Configuración del microservicio Redis
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Cache Configuration
    CACHE_DEFAULT_TTL = int(os.getenv('CACHE_DEFAULT_TTL', 3600))  # 1 hora
    CACHE_MAX_ENTRIES = int(os.getenv('CACHE_MAX_ENTRIES', 10000))
    
    # Queue Configuration
    QUEUE_CHANNEL = os.getenv('QUEUE_CHANNEL', 'inventarios_updates')
    
    @property
    def REDIS_URL(self):
        """Construir URL de Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
