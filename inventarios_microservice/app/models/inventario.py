from . import db
import uuid

class Inventario(db.Model):
    __tablename__ = "inventarios"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Key a la tabla productos (misma base de datos compartida)
    # ondelete='RESTRICT' previene borrar productos con inventario
    # onupdate='CASCADE' actualiza automáticamente si cambia el ID del producto
    producto_id = db.Column(
        db.Integer,  # Mismo tipo que productos.id
        db.ForeignKey('productos.id', ondelete='RESTRICT', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    
    cantidad = db.Column(db.Integer, nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)

    # Auditoría
    usuario_creacion = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    usuario_actualizacion = db.Column(db.String(100), nullable=True)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    
    # Índice único para evitar duplicados de producto-ubicación
    __table_args__ = (
        db.UniqueConstraint('producto_id', 'ubicacion', name='uq_producto_ubicacion'),
        db.Index('idx_ubicacion', 'ubicacion'),
    )
