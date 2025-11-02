"""
Redis Service - Microservicio para Cache y Cola con Redis
Puerto: 5011
"""
from flask import Flask
from app.config.config import Config
from app.services.redis_service import redis_client


def create_app(config_class=Config):
    """Factory pattern para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar Redis
    redis_client.init_app(app)
    
    # Registrar blueprints
    from app.routes.cache import cache_bp
    from app.routes.queue import queue_bp
    from app.routes.health import health_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(cache_bp, url_prefix='/api/cache')
    app.register_blueprint(queue_bp, url_prefix='/api/queue')
    
    # Manejo de errores global
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Recurso no encontrado'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Error interno del servidor'}, 500
    
    return app
