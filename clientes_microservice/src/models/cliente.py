from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class Cliente(db.Model):
    """
    Modelo de cliente
    """
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    nombre_contacto = db.Column(db.String(100), nullable=False)
    cargo_contacto = db.Column(db.String(100), nullable=False)
    correo_contacto = db.Column(db.String(120), nullable=False)
    correo_empresa = db.Column(db.String(120), nullable=True)
    telefono_contacto = db.Column(db.String(50), nullable=False)
    nit = db.Column(db.String(50), nullable=False, unique=True)
    direccion = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, nombre, tipo, pais, nombre_contacto, cargo_contacto, correo_contacto, telefono_contacto, nit, direccion, correo_empresa):
        self.nombre = nombre
        self.tipo = tipo
        self.pais = pais
        self.nombre_contacto = nombre_contacto
        self.cargo_contacto = cargo_contacto
        self.correo_empresa = correo_empresa
        self.telefono_contacto = telefono_contacto
        self.nit = nit
        self.direccion = direccion
        self.nombre = nombre
        self.tipo = tipo
        self.pais = pais
        self.nombre_contacto = nombre_contacto
        self.cargo_contacto = cargo_contacto
        self.correo_contacto = correo_contacto
        self.telefono_contacto = telefono_contacto
        self.nit = nit
    
    def to_dict(self):
        """Convierte el cliente a diccionario (sin contraseña)"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'pais': self.pais,
            'contacto': {
                'nombre': self.nombre_contacto,
                'cargo': self.cargo_contacto,
                'correo': self.correo_contacto,
                'telefono': self.telefono_contacto,
            },
            'nit': self.nit,
            'correo': self.correo_empresa,
            'direccion': self.direccion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def save(self):
        """Guarda el cliente en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Elimina el cliente de la base de datos"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Cliente {self.correo_contacto}>'
