from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .inventario import Inventario
from .producto import Producto  # Importar para desarrollo local

__all__ = ['db', 'Inventario', 'Producto']
