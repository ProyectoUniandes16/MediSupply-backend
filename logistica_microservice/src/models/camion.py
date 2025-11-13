from src import db
import uuid


class Camion(db.Model):
    """Modelo para camiones disponibles por bodega"""
    __tablename__ = 'camiones'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    placa = db.Column(db.String(20), nullable=False, unique=True)
    capacidad_kg = db.Column(db.Float, nullable=False)
    capacidad_m3 = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='disponible')  # disponible, en_ruta, mantenimiento
    
    # Foreign keys
    bodega_id = db.Column(db.String(36), db.ForeignKey('bodegas.id'), nullable=False)
    tipo_camion_id = db.Column(db.String(36), db.ForeignKey('tipos_camion.id'), nullable=False)
    
    # Relaciones
    bodega = db.relationship('Bodega', back_populates='camiones')
    tipo_camion = db.relationship('TipoCamion', back_populates='camiones')
    
    def __init__(self, placa, capacidad_kg, capacidad_m3, bodega_id, tipo_camion_id, estado='disponible'):
        self.id = str(uuid.uuid4())
        self.placa = placa
        self.capacidad_kg = capacidad_kg
        self.capacidad_m3 = capacidad_m3
        self.bodega_id = bodega_id
        self.tipo_camion_id = tipo_camion_id
        self.estado = estado
    
    def to_dict(self):
        """Serializa el camión a diccionario"""
        return {
            'id': self.id,
            'placa': self.placa,
            'capacidad_kg': self.capacidad_kg,
            'capacidad_m3': self.capacidad_m3,
            'estado': self.estado,
            'bodega_id': self.bodega_id,
            'tipo_camion_id': self.tipo_camion_id
        }
    
    def to_dict_with_tipo(self):
        """Serializa el camión con información del tipo"""
        data = self.to_dict()
        if self.tipo_camion:
            data['tipo_camion'] = self.tipo_camion.to_dict()
        return data
    
    def to_dict_with_bodega(self):
        """Serializa el camión con información de la bodega"""
        data = self.to_dict()
        if self.bodega:
            data['bodega'] = self.bodega.to_dict()
        return data
    
    def __repr__(self):
        return f'<Camion {self.placa}>'
