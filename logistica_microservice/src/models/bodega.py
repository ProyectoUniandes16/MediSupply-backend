from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from src.models.zona import db

class Bodega(db.Model):
    """
    Modelo de Bodega
    """
    __tablename__ = 'bodegas'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con camiones
    camiones = db.relationship('Camion', back_populates='bodega', lazy=True)

    def __init__(self, nombre, ubicacion):
        self.nombre = nombre
        self.ubicacion = ubicacion

    def to_dict(self):
        """Convierte la bodega a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ubicacion': self.ubicacion,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_dict_with_zonas(self):
        """Convierte la bodega a diccionario incluyendo sus zonas"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ubicacion': self.ubicacion,
            'zonas': [zona.to_dict() for zona in self.zonas.all()],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_dict_with_camiones(self):
        """Convierte la bodega a diccionario incluyendo sus camiones"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ubicacion': self.ubicacion,
            'camiones': [camion.to_dict_with_tipo() for camion in self.camiones],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def save(self):
        """Guarda la bodega en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Elimina la bodega de la base de datos"""
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<Bodega {self.nombre}>'
