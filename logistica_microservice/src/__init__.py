from flask import Flask
from flask_jwt_extended import JWTManager
from src.config.config import Config
from src.models.zona import db
from src.blueprints.health import health_bp
from src.blueprints.zonas import zonas_bp
from src.blueprints.bodegas import bodegas_bp
from src.blueprints.visitas import visitas_bp

def create_app(config_class=Config):
    """
    Factory function para crear la aplicación Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Configurar JWT para manejar identity como string
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return str(user_id)
    
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(zonas_bp)
    app.register_blueprint(bodegas_bp)
    app.register_blueprint(visitas_bp)
    
    # Crear tablas de la base de datos
    with app.app_context():
        db.create_all()
    
    return app
