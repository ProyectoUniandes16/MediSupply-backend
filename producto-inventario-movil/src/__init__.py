from flask import Flask
from flask_jwt_extended import JWTManager
from src.config.config import Config
from src.blueprints.health import health_bp
from src.blueprints.producto import producto_bp
from src.blueprints.pedidos import pedidos_bp

import logging
import os
import sys

def create_app(config_class=Config):
    """
    Factory function para crear la aplicación Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Configurar logging raíz de la aplicación. Usamos la variable de entorno
    # LOG_LEVEL (o el valor en config) para controlar el verbosidad.
    log_level_str = os.environ.get('LOG_LEVEL', app.config.get('LOG_LEVEL', 'INFO')).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    # Asegurarnos que el logger de Flask tiene al menos ese nivel
    app.logger.setLevel(log_level)
    
    # Inicializar JWT
    JWTManager(app)
    
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(producto_bp)
    app.register_blueprint(pedidos_bp)
    
    return app
