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
    nombre_contacto = db.Column(db.String(150), nullable=True)
    latitud = db.Column(db.Numeric(10, 7), nullable=True)
    longitud = db.Column(db.Numeric(10, 7), nullable=True)
    fecha_fin_visita = db.Column(db.DateTime, nullable=True)
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
            "nombre_contacto": self.nombre_contacto,
            "latitud": float(self.latitud) if self.latitud is not None else None,
            "longitud": float(self.longitud) if self.longitud is not None else None,
            "fecha_fin_visita": self.fecha_fin_visita.isoformat() if self.fecha_fin_visita else None,
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
