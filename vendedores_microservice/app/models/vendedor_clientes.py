from . import db

class VendedorClientes(db.Model):
    __tablename__ = "vendedor_clientes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vendedor_id = db.Column(db.String(36), db.ForeignKey("vendedores.id"), nullable=False)
    cliente_id = db.Column(db.String(36), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "vendedor_id": self.vendedor_id,
            "cliente_id": self.cliente_id,
        }

    @classmethod
    def get_cliente_ids_by_vendedor(cls, vendedor_id, session=None):
        """Devuelve una lista de `cliente_id` asociados al `vendedor_id`.

        Args:
            vendedor_id (str): id del vendedor a consultar.
            session (Session, optional): sesión de SQLAlchemy. Si no se proporciona,
                se usa `db.session`.

        Returns:
            List[str]: lista de cliente_id (puede estar vacía).
        """
        sess = session or db.session
        rows = sess.query(cls).filter_by(vendedor_id=vendedor_id).all()
        return [r.cliente_id for r in rows]