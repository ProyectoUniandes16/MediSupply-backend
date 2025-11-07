from app.extensions import db
from datetime import datetime

# Estados válidos del video
ESTADOS_VIDEO = ['cargando', 'cargado', 'procesando', 'procesado', 'error']

class VideoEvidencia(db.Model):
    """
    Modelo para almacenar evidencias de video de productos
    Registra metadatos del video y tracking del procesamiento
    """
    __tablename__ = "videos_evidencia"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    
    # Información del archivo original
    nombre_original = db.Column(db.String(255), nullable=False)
    nombre_archivo_minio = db.Column(db.String(255), nullable=False)  # Nombre único en MinIO
    tamaño_archivo = db.Column(db.Integer, nullable=False)  # Tamaño en bytes
    formato_original = db.Column(db.String(10), nullable=False)  # MP4, MOV, AVI
    
    # Descripción
    descripcion = db.Column(db.Text, nullable=True)
    
    # Estado del procesamiento
    estado = db.Column(db.String(20), nullable=False, default='cargando')  # cargando, cargado, procesando, procesado, error
    
    # Rutas en MinIO
    ruta_original = db.Column(db.String(500), nullable=False)  # videos/original/{producto_id}/{nombre}
    ruta_procesado_pc = db.Column(db.String(500), nullable=True)  # videos/procesado/{producto_id}/{nombre}_procesado_pc.mp4
    ruta_procesado_mobile = db.Column(db.String(500), nullable=True)  # videos/procesado/{producto_id}/{nombre}_procesado_mobile.mp4
    
    # URLs presigned (temporal, regenerar cuando se requiera)
    url_reproduccion = db.Column(db.String(1000), nullable=True)
    url_expiracion = db.Column(db.DateTime, nullable=True)
    
    # Auditoría
    usuario_registro = db.Column(db.String(120), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_procesado = db.Column(db.DateTime, nullable=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Mensajes de error si ocurren
    mensaje_error = db.Column(db.Text, nullable=True)
    
    # Relación con producto
    producto = db.relationship('Producto', backref=db.backref('videos', lazy=True))

    def __repr__(self):
        return f"<VideoEvidencia {self.nombre_original} - Estado: {self.estado}>"
    
    def esta_procesado(self):
        """Verifica si el video ya fue procesado"""
        return self.estado == 'procesado'
    
    def marcar_como_cargado(self):
        """Marca el video como cargado exitosamente"""
        self.estado = 'cargado'
    
    def marcar_como_procesando(self):
        """Marca el video como en procesamiento"""
        self.estado = 'procesando'
    
    def marcar_como_procesado(self, ruta_pc=None, ruta_mobile=None):
        """Marca el video como procesado exitosamente"""
        self.estado = 'procesado'
        self.fecha_procesado = datetime.utcnow()
        if ruta_pc:
            self.ruta_procesado_pc = ruta_pc
        if ruta_mobile:
            self.ruta_procesado_mobile = ruta_mobile
    
    def marcar_error(self, mensaje):
        """Marca el video con error"""
        self.estado = 'error'
        self.mensaje_error = mensaje
    
    def to_dict(self):
        """Serializa el video a diccionario"""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'nombre_original': self.nombre_original,
            'tamaño_archivo': self.tamaño_archivo,
            'formato_original': self.formato_original,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'usuario_registro': self.usuario_registro,
            'fecha_subida': self.fecha_subida.strftime("%Y-%m-%d %H:%M:%S"),
            'fecha_procesado': self.fecha_procesado.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_procesado else None,
            'url_reproduccion': self.url_reproduccion if self.esta_procesado() else None,
            'mensaje_error': self.mensaje_error
        }
