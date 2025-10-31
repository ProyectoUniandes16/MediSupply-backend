from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from sqlalchemy import true

db = SQLAlchemy()

class Pedido(db.Model):
    """
    Modelo de pedido
    """
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    # Store related entity IDs without enforcing cross-service foreign key constraints
    # (other microservices manage their own tables). Using plain columns avoids
    # SQLAlchemy trying to resolve tables that are defined in other services.
    cliente_id = db.Column(db.Integer, nullable=False)
    vendedor_id = db.Column(db.String, nullable=True)
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, cliente_id, estado, total, vendedor_id):
        self.cliente_id = cliente_id
        self.estado = estado
        self.total = total
        self.vendedor_id = vendedor_id

    def to_dict(self):
        """Convierte el pedido a diccionario"""
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'fecha_pedido': self.fecha_pedido.isoformat(),
            'estado': self.estado,
            'total': self.total,
            'vendedor_id': self.vendedor_id
        }
    
    def save(self):
        """Guarda el pedido en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Elimina el pedido de la base de datos"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Pedido {self.id}>'

    