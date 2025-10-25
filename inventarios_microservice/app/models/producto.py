from . import db

class Producto(db.Model):
    """
    Modelo de Producto para desarrollo/pruebas locales.
    En producción, esta tabla existe en el microservicio de productos.
    """
    __tablename__ = "productos"

    id = db.Column(db.String(100), primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    sku = db.Column(db.String(100), unique=True, nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Auditoría
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    
    def __repr__(self):
        return f'<Producto {self.id} - {self.nombre}>'
