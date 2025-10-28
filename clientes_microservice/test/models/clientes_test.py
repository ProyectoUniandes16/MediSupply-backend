import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from src.models.cliente import db, Cliente

# Suponiendo que tienes el modelo Cliente ya importado
# from tu_modulo import db, Cliente 

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session

def test_cliente_save_y_to_dict(session):
    cliente = Cliente(
        nombre="Empresa S.A.",
        tipo="Sociedad Anónima",
        pais="México",
        nombre_contacto="Juan Pérez",
        cargo_contacto="Gerente",
        correo_contacto="juan@empresa.com",
        correo_empresa="contacto@empresa.com",
        telefono_contacto="5551234567",
        nit="A1B2C3D4E5",
        direccion="Calle Falsa 123"
    )
    cliente.save()
    assert cliente.id is not None  # Se asignó el ID en la DB
    dict_cliente = cliente.to_dict()
    assert dict_cliente["nombre"] == "Empresa S.A."
    assert dict_cliente["contacto"]["correo"] == "juan@empresa.com"

def test_cliente_delete(session):
    cliente = Cliente(
        nombre="Empresa X",
        tipo="Sociedad Limitada",
        pais="Colombia",
        nombre_contacto="Ana Gómez",
        cargo_contacto="Directora",
        correo_contacto="ana@empresa.com",
        correo_empresa="contacto@empresa.com",
        telefono_contacto="3219876543",
        nit="X6Y7Z8W9V0",
        direccion="Avenida Siempreviva 742"
    )
    cliente.save()
    id_cliente = cliente.id
    cliente.delete()
    resultado = session.get(Cliente, id_cliente)  # Uso del método moderno
    assert resultado is None

def test_cliente_unique_nit(session):
    cliente_1 = Cliente(
        nombre="Uno",
        tipo="Freelancer",
        pais="Guatemala",
        nombre_contacto="Laura Barrera",
        cargo_contacto="Consultor",
        correo_contacto="laura@email.com",
        correo_empresa="contacto@empresa.com",
        telefono_contacto="1112223333",
        nit="UNIQUE123",
        direccion="Zona 1"
    )
    cliente_1.save()
    cliente_2 = Cliente(
        nombre="Dos",
        tipo="Empresa",
        pais="Guatemala",
        nombre_contacto="Mario Ruiz",
        cargo_contacto="Director",
        correo_contacto="mario@email.com",
        correo_empresa="contacto@empresa.com",
        telefono_contacto="4445556666",
        nit="UNIQUE123",  # mismo NIT
        direccion="Zona 2"
    )
    with pytest.raises(Exception):
        cliente_2.save()
