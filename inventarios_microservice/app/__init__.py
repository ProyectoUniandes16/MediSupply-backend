import os
from flask import Flask
from flask_cors import CORS
from app.models import db


def create_app():
    """Factory pattern para crear la aplicación Flask."""
    app = Flask(__name__)

    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://medisupply_user:medisupply_password@localhost:5432/medisupply'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = os.getenv('SQLALCHEMY_ECHO', 'False') == 'True'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Configuración de Redis Service
    app.config['REDIS_SERVICE_URL'] = os.getenv('REDIS_SERVICE_URL', 'http://localhost:5011')
    
    # CORS
    CORS(app)

    # Inicializar extensiones
    db.init_app(app)

    # Registrar blueprints
    from app.routes.health import bp_health
    from app.routes.inventarios import bp_inventarios
    from app.routes.errors import register_error_handlers

    app.register_blueprint(bp_health)
    app.register_blueprint(bp_inventarios, url_prefix='/api/inventarios')
    
    # Registrar manejadores de errores
    register_error_handlers(app)

    # Crear las tablas si no existen
    with app.app_context():
        # Primero reflejar las tablas existentes para reconocer la tabla productos
        db.Model.metadata.reflect(bind=db.engine, only=['productos'])
        # Luego crear las tablas de este microservicio
        db.create_all()

    return app
