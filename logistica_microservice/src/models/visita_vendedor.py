from datetime import datetime
from src.models.zona import db


class VisitaVendedor(db.Model):
    """Modelo que representa una visita planificada de un vendedor a un cliente."""
    __tablename__ = "visitas_vendedor"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cliente_id = db.Column(db.Integer, nullable=False, index=True)
    vendedor_id = db.Column(db.String(36), nullable=False, index=True)
    fecha_visita = db.Column(db.Date, nullable=False)
    estado = db.Column(
        db.Enum("pendiente", "en progreso", "finalizado", name="estado_visita"),
        nullable=False,
        default="pendiente",
    )
    comentarios = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "cliente_id",
            "vendedor_id",
            "fecha_visita",
            name="uq_visita_cliente_vendedor_fecha",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "vendedor_id": self.vendedor_id,
            "fecha_visita": self.fecha_visita.isoformat(),
            "estado": self.estado,
            "comentarios": self.comentarios,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def __repr__(self):
        return (
            f"<VisitaVendedor cliente_id={self.cliente_id} vendedor_id={self.vendedor_id} "
            f"fecha_visita={self.fecha_visita}>"
        )
