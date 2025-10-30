
from calendar import c

from flask import current_app
from src.models.pedios import Pedido
from src.models.pedidos_productos import PedidoProducto


class PedidoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de pedidos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def registrar_pedido(data):
    """
    Función para registrar un nuevo pedido
    """

    if data is None:
        raise PedidoServiceError({'error': 'No se proporcionaron datos'}, 400)

    required_fields = ['cliente_id', 'total', 'productos']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise PedidoServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)
    
    if (data['total'] <= 0):
        raise PedidoServiceError({'error': 'El total del pedido debe ser mayor que cero', 'codigo': 'TOTAL_MENOR_CERO'}, 400)
    
    if (data['productos'] == []):
        raise PedidoServiceError({'error': 'El pedido debe contener al menos un producto', 'codigo': 'PRODUCTOS_VACIO'}, 400)

    try:
        pedido = Pedido(
            cliente_id=data['cliente_id'],
            estado='pendiente',
            total=data['total'],
            vendedor_id=data.get('vendedor_id')
        )
        pedido.save()
        for prod in data['productos']:
            pedido_producto = PedidoProducto(
                pedido_id=pedido.id,
                producto_id=prod['id'],
                cantidad=prod['cantidad'],
                precio=prod['precio']
            )
            pedido_producto.save()
        
        return pedido.to_dict()
    except Exception as e:
        current_app.logger.error(f"Error al guardar el pedido: {str(e)}")
        raise PedidoServiceError({'error': 'Error al guardar el pedido', 'codigo': 'ERROR_GUARDAR_PEDIDO'}, 500)
    
