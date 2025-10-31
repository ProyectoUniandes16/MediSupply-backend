from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .vendedor import Vendedor
from .plan_venta import PlanVenta
from .plan_vendedor import PlanVendedor
from .asignacion import AsignacionZona
