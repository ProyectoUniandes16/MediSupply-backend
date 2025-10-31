"""
Tabla intermedia para la relación Many-to-Many entre PlanVenta y Vendedor
"""
from . import db


class PlanVendedor(db.Model):
    """
    Tabla de asociación entre planes de venta y vendedores.
    Permite que un plan tenga múltiples vendedores asignados.
    """
    __tablename__ = "plan_vendedor"
    
    id = db.Column(db.String(36), primary_key=True)
    plan_id = db.Column(
        db.String(36), 
        db.ForeignKey("planes_venta.id", ondelete="CASCADE"), 
        nullable=False
    )
    vendedor_id = db.Column(
        db.String(36), 
        db.ForeignKey("vendedores.id", ondelete="CASCADE"), 
        nullable=False
    )
    fecha_asignacion = db.Column(
        db.DateTime, 
        nullable=False, 
        server_default=db.func.now()
    )
    
    # Constraint único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint("plan_id", "vendedor_id", name="uq_plan_vendedor"),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "vendedor_id": self.vendedor_id,
            "fecha_asignacion": self.fecha_asignacion.isoformat()
        }
