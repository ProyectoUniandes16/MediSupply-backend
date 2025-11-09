from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

# Tabla de asociación entre Zona y Bodega (relación muchos a muchos)
zona_bodega = db.Table('zona_bodega',
    db.Column('zona_id', db.String(36), db.ForeignKey('zonas.id'), primary_key=True),
    db.Column('bodega_id', db.String(36), db.ForeignKey('bodegas.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False)
)

class Zona(db.Model):
    """
    Modelo de Zona de distribución
    """
    __tablename__ = 'zonas'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    latitud_maxima = db.Column(db.Float, nullable=False)
    latitud_minima = db.Column(db.Float, nullable=False)
    longitud_maxima = db.Column(db.Float, nullable=False)
    longitud_minima = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relación muchos a muchos con Bodega
    bodegas = db.relationship('Bodega', secondary=zona_bodega, lazy='dynamic',
                              backref=db.backref('zonas', lazy='dynamic'))

    def __init__(self, nombre, latitud_maxima, latitud_minima, longitud_maxima, longitud_minima):
        self.nombre = nombre
        self.latitud_maxima = latitud_maxima
        self.latitud_minima = latitud_minima
        self.longitud_maxima = longitud_maxima
        self.longitud_minima = longitud_minima

    def to_dict(self):
        """Convierte la zona a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'latitud_maxima': self.latitud_maxima,
            'latitud_minima': self.latitud_minima,
            'longitud_maxima': self.longitud_maxima,
            'longitud_minima': self.longitud_minima,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_dict_with_bodegas(self):
        """Convierte la zona a diccionario incluyendo sus bodegas"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'latitud_maxima': self.latitud_maxima,
            'latitud_minima': self.latitud_minima,
            'longitud_maxima': self.longitud_maxima,
            'longitud_minima': self.longitud_minima,
            'bodegas': [bodega.to_dict() for bodega in self.bodegas.all()],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def save(self):
        """Guarda la zona en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Elimina la zona de la base de datos"""
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<Zona {self.nombre}>'
