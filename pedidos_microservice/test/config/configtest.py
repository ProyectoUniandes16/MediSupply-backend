import pytest
from flask import Flask
from src.models import db  # Ajusta este import según tu estructura real

@pytest.fixture(scope='module')
def app():
    """Crea y configura la app Flask para tests con base de datos en memoria."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
