from datetime import datetime

# Reuse the SQLAlchemy instance defined in src.models.pedios to avoid
# registering multiple instances on the same Flask app during tests.
from src.models.pedios import db

class PedidoProducto(db.Model):
    """
    Modelo de productos en un pedido
    """
    __tablename__ = 'pedido_producto'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, nullable=False)
    producto_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)

    def __init__(self, pedido_id, producto_id, cantidad, precio):
        self.pedido_id = pedido_id
        self.producto_id = producto_id
        self.cantidad = cantidad
        self.precio = precio

    def to_dict(self):
        """Convierte el producto del pedido a diccionario"""
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'producto_id': self.producto_id,
            'cantidad': self.cantidad,
            'precio': self.precio,
        }
    
    def save(self):
        """Guarda el producto del pedido en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Elimina el producto del pedido de la base de datos"""
        db.session.delete(self)
        db.session.commit()

