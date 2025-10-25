import os
from flask import Flask
from app.models import db


def create_app():
    """Factory pattern para crear la aplicación Flask."""
    app = Flask(__name__)

    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/inventarios_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = os.getenv('SQLALCHEMY_ECHO', 'False') == 'True'

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
        db.create_all()

    return app
