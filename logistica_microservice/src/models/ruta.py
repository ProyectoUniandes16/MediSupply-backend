from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from src.models.zona import db

class Ruta(db.Model):
    """
    Modelo de Ruta de entrega
    """
    __tablename__ = 'rutas'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bodega_id = db.Column(db.String(36), db.ForeignKey('bodegas.id'), nullable=False)
    camion_id = db.Column(db.String(36), db.ForeignKey('camiones.id'), nullable=False)
    zona_id = db.Column(db.String(36), db.ForeignKey('zonas.id'), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')  # pendiente, iniciado, en_progreso, completado, cancelado
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    bodega = db.relationship('Bodega', backref=db.backref('rutas', lazy='dynamic'))
    camion = db.relationship('Camion', backref=db.backref('rutas', lazy='dynamic'))
    zona = db.relationship('Zona', backref=db.backref('rutas', lazy='dynamic'))
    detalles = db.relationship('DetalleRuta', backref='ruta', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, bodega_id, camion_id, zona_id, estado='pendiente'):
        self.bodega_id = bodega_id
        self.camion_id = camion_id
        self.zona_id = zona_id
        self.estado = estado
        if estado == 'iniciado':
            self.fecha_inicio = datetime.utcnow()

    def to_dict(self):
        """Convierte la ruta a diccionario"""
        return {
            'id': self.id,
            'bodega_id': self.bodega_id,
            'camion_id': self.camion_id,
            'zona_id': self.zona_id,
            'estado': self.estado,
            'fecha_asignacion': self.fecha_asignacion.isoformat(),
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_dict_with_details(self):
        """Convierte la ruta a diccionario incluyendo los detalles ordenados y datos enriquecidos de bodega, camión y zona"""
        detalles_ordenados = self.detalles.order_by(DetalleRuta.orden.asc()).all()
        
        # Construir información de bodega
        bodega_info = {
            'id': self.bodega.id,
            'nombre': self.bodega.nombre,
            'ubicacion': self.bodega.ubicacion if hasattr(self.bodega, 'ubicacion') else None
        }
        
        # Construir información de camión (la capacidad está en Camion, no en TipoCamion)
        camion_info = {
            'id': self.camion.id,
            'placa': self.camion.placa,
            'capacidad_kg': self.camion.capacidad_kg,
            'capacidad_m3': self.camion.capacidad_m3,
            'estado': self.camion.estado,
            'disponible': self.camion.disponible
        }
        
        # Agregar información del tipo de camión si existe
        if self.camion.tipo_camion:
            camion_info['tipo'] = {
                'id': self.camion.tipo_camion.id,
                'nombre': self.camion.tipo_camion.nombre,
                'descripcion': self.camion.tipo_camion.descripcion
            }
        
        # Construir información de zona
        zona_info = {
            'id': self.zona.id,
            'nombre': self.zona.nombre,
            'descripcion': self.zona.descripcion if hasattr(self.zona, 'descripcion') else None
        }
        
        return {
            'id': self.id,
            'bodega_id': self.bodega_id,
            'bodega': bodega_info,
            'camion_id': self.camion_id,
            'camion': camion_info,
            'zona_id': self.zona_id,
            'zona': zona_info,
            'estado': self.estado,
            'fecha_asignacion': self.fecha_asignacion.isoformat(),
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'detalles': [detalle.to_dict() for detalle in detalles_ordenados],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def save(self):
        """Guarda la ruta en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Elimina la ruta de la base de datos"""
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<Ruta {self.id} - Estado: {self.estado}>'


class DetalleRuta(db.Model):
    """
    Modelo de Detalle de Ruta (puntos de entrega en la ruta)
    """
    __tablename__ = 'detalles_ruta'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ruta_id = db.Column(db.String(36), db.ForeignKey('rutas.id'), nullable=False)
    orden = db.Column(db.Integer, nullable=False)  # Orden de visita en la ruta
    pedido_id = db.Column(db.String(36), nullable=False)  # ID del pedido asociado
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')  # pendiente, visitado, omitido
    fecha_visita = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, ruta_id, orden, pedido_id, latitud, longitud, estado='pendiente'):
        self.ruta_id = ruta_id
        self.orden = orden
        self.pedido_id = pedido_id
        self.latitud = latitud
        self.longitud = longitud
        self.estado = estado

    def to_dict(self):
        """Convierte el detalle de ruta a diccionario"""
        return {
            'id': self.id,
            'ruta_id': self.ruta_id,
            'orden': self.orden,
            'pedido_id': self.pedido_id,
            'ubicacion': [self.longitud, self.latitud],
            'estado': self.estado,
            'fecha_visita': self.fecha_visita.isoformat() if self.fecha_visita else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def save(self):
        """Guarda el detalle de ruta en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self

    def __repr__(self):
        return f'<DetalleRuta {self.id} - Orden: {self.orden}>'
