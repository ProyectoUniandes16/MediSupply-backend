from . import db

class Inventario(db.Model):
    __tablename__ = "inventarios"

    id = db.Column(db.String(36), primary_key=True)
    
    # Clave foránea a la tabla productos
    # En desarrollo local sin relación estricta, en producción con FK real
    producto_id = db.Column(
        db.String(100), 
        db.ForeignKey('productos.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True  # Índice para mejorar búsquedas
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
