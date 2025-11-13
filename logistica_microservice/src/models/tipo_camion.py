from src import db
import uuid


class TipoCamion(db.Model):
    """Modelo para tipos de camión de transporte"""
    __tablename__ = 'tipos_camion'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))
    
    # Relación con camiones
    camiones = db.relationship('Camion', back_populates='tipo_camion', lazy=True)
    
    def __init__(self, nombre, descripcion=None):
        self.id = str(uuid.uuid4())
        self.nombre = nombre
        self.descripcion = descripcion
    
    def to_dict(self):
        """Serializa el tipo de camión a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }
    
    def __repr__(self):
        return f'<TipoCamion {self.nombre}>'
