import pytest
from flask import Flask

# Each model module defines its own SQLAlchemy() instance. Initialize both
# against the test app so the model.save()/commit() calls work.
from src.models.pedios import db as pedidos_db
import src.models.pedidos_productos as pedidos_productos_module
from src.blueprints.pedidos import pedidos_bp


@pytest.fixture(scope='module')
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Use the single SQLAlchemy instance from pedidos to back the other model
    # module (the code defines a separate `db` there, but reusing the same
    # instance avoids registering multiple SQLAlchemy instances on the app
    # which raises an error).
    pedidos_productos_module.db = pedidos_db

    pedidos_db.init_app(app)

    # register pedidos blueprint for route tests
    app.register_blueprint(pedidos_bp)

    with app.app_context():
        # Ensure there's a lightweight `productos` table to satisfy the
        # foreign key on PedidoProducto (other microservice owns that table
        # in production). Define the table in the shared metadata so
        # create_all() will create it in the in-memory SQLite DB.
        from sqlalchemy import Table, Column, Integer

        # Avoid redefining the table if another test module already added it
        if 'productos' not in pedidos_db.metadata.tables:
            Table(
                'productos',
                pedidos_db.metadata,
                Column('id', Integer, primary_key=True),
            )

        # create tables for models bound to the shared SQLAlchemy instance
        pedidos_db.create_all()
        yield app
        pedidos_db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    # return the pedidos_db session for DB assertions in tests
    with app.app_context():
        yield pedidos_db.session
