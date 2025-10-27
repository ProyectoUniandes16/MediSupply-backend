from . import db

class PlanVenta(db.Model):
    __tablename__ = "planes_venta"

    id = db.Column(db.String(36), primary_key=True)
    nombre_plan = db.Column(db.String(200), nullable=False)
    gerente_id = db.Column(db.String(36), nullable=False)  # ID del gerente comercial
    vendedor_id = db.Column(db.String(36), db.ForeignKey("vendedores.id", ondelete="CASCADE"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False)  # YYYY-MM
    
    # Metas/Objetivos
    meta_ingresos = db.Column(db.Numeric(14, 2), nullable=False)  # Objetivo de ingresos
    meta_visitas = db.Column(db.Integer, nullable=False)  # Objetivo de visitas
    meta_clientes_nuevos = db.Column(db.Integer, nullable=False)  # Objetivo de clientes nuevos
    
    estado = db.Column(db.String(20), nullable=False, default="activo")
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    vendedor = db.relationship("Vendedor", back_populates="planes")
    __table_args__ = (db.UniqueConstraint("vendedor_id", "periodo", name="uq_planes_venta_vendedor_periodo"),)
    
    def to_dict(self):
        return {
            "id": self.id,
            "nombre_plan": self.nombre_plan,
            "gerente_id": self.gerente_id,
            "vendedor_id": self.vendedor_id,
            "periodo": self.periodo,
            "meta_ingresos": float(self.meta_ingresos),
            "meta_visitas": self.meta_visitas,
            "meta_clientes_nuevos": self.meta_clientes_nuevos,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_actualizacion": self.fecha_actualizacion.isoformat(),
        }