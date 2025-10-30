from . import db


class PlanVenta(db.Model):
    __tablename__ = "planes_venta"

    id = db.Column(db.String(36), primary_key=True)
    nombre_plan = db.Column(db.String(200), nullable=False)
    gerente_id = db.Column(db.String(36), nullable=False)  # ID del gerente comercial
    periodo = db.Column(db.String(7), nullable=False)  # YYYY-MM
    
    # Metas/Objetivos
    meta_ingresos = db.Column(db.Numeric(14, 2), nullable=False)  # Objetivo de ingresos
    meta_visitas = db.Column(db.Integer, nullable=False)  # Objetivo de visitas
    meta_clientes_nuevos = db.Column(db.Integer, nullable=False)  # Objetivo de clientes nuevos
    
    estado = db.Column(db.String(20), nullable=False, default="activo")
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relación Many-to-Many con Vendedores a través de PlanVendedor
    vendedores = db.relationship(
        "Vendedor",
        secondary="plan_vendedor",
        back_populates="planes",
        lazy="selectin"
    )
    
    # Relación con la tabla intermedia para acceso directo
    plan_vendedores = db.relationship(
        "PlanVendedor",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def to_dict(self, include_vendedores=False):
        """
        Convierte el plan a diccionario.
        
        Args:
            include_vendedores: Si True, incluye la información completa de vendedores
        """
        data = {
            "id": self.id,
            "nombre_plan": self.nombre_plan,
            "gerente_id": self.gerente_id,
            "periodo": self.periodo,
            "meta_ingresos": float(self.meta_ingresos),
            "meta_visitas": self.meta_visitas,
            "meta_clientes_nuevos": self.meta_clientes_nuevos,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_actualizacion": self.fecha_actualizacion.isoformat(),
        }
        
        if include_vendedores and self.vendedores:
            data["vendedores"] = [
                {
                    "id": v.id,
                    "nombre": v.nombre,
                    "apellidos": v.apellidos,
                    "correo": v.correo,
                    "zona": v.zona
                }
                for v in self.vendedores
            ]
            data["vendedores_ids"] = [v.id for v in self.vendedores]
        
        return data