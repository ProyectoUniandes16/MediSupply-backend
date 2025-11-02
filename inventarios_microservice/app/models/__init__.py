from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .inventario import Inventario

__all__ = ['db', 'Inventario']
