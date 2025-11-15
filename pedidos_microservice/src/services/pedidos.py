
from flask import current_app
from src.models.pedidos_productos import PedidoProducto
from src.models.pedios import Pedido


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
    # Consider a field missing only if it's not present or its value is None.
    # This allows numeric values like 0 to be valid inputs (total == 0 will be
    # validated by the subsequent business rule) and avoids treating empty
    # strings/lists as missing when the caller intended to pass them.
    missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]
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
    

def listar_pedidos(vendedor_id=None, cliente_id=None, estado=None):
    """
    Lista pedidos. Filtros opcionales por vendedor_id, cliente_id y estado.
    Ordena por fecha_pedido descendente para mostrar historial más reciente primero.

    Args:
        vendedor_id (str|int|None): id del vendedor para filtrar
        cliente_id (int|None): id del cliente para filtrar
        estado (str|None): estado del pedido (pendiente, en_proceso, despachado, entregado, cancelado)

    Returns:
        dict: {'data': [ ... ]}
    """
    try:
        query = Pedido.query

        # Apply filters only when provided (not None and not empty string)
        if vendedor_id is not None and str(vendedor_id) != '':
            # vendedor_id is stored as string in the model; compare as string
            query = query.filter(Pedido.vendedor_id == str(vendedor_id))

        if cliente_id is not None and str(cliente_id) != '':
            try:
                cliente_int = int(cliente_id)
            except Exception:
                # if cannot convert, keep as-is so filter will likely not match
                cliente_int = cliente_id
            query = query.filter(Pedido.cliente_id == cliente_int)

        if estado is not None and str(estado).strip() != '':
            query = query.filter(Pedido.estado == str(estado).strip())

        # Orden por fecha de creación (desc)
        query = query.order_by(Pedido.fecha_pedido.desc())
        pedidos = query.all()
        resultado = []
        for pedido in pedidos:
            item = pedido.to_dict()
            pedido_productos = PedidoProducto.query.filter(PedidoProducto.pedido_id == pedido.id).count()
            item['total_productos'] = pedido_productos
            resultado.append(item)
        return {'data': resultado}
    except PedidoServiceError:
        # allow service errors to bubble up
        raise
    except Exception as e:
        current_app.logger.error(f"Error al listar pedidos: {str(e)}")
        raise PedidoServiceError({'error': 'Error al listar pedidos', 'codigo': 'ERROR_LISTAR_PEDIDOS'}, 500)


def detalle_pedido(pedido_id):
    """
    Obtiene el detalle de un pedido por su ID.
    Args:
        pedido_id (int): ID del pedido
    Returns:
        dict: {'data': ...}
    """
    try:

        query = Pedido.query.filter(Pedido.id == pedido_id)
        pedido = query.first()
        resultado = {}
        resultado = pedido.to_dict()
        pedido_productos = PedidoProducto.query.filter(PedidoProducto.pedido_id == pedido.id).all()
        productos_list = []
        for pp in pedido_productos:
            productos_list.append(pp.to_dict())
        resultado['productos'] = productos_list
        return {'data': resultado}
    except PedidoServiceError:
        # allow service errors to bubble up
        raise
    except Exception as e:
        current_app.logger.error(f"Error al listar pedidos: {str(e)}")
        raise PedidoServiceError({'error': 'Error al listar pedidos', 'codigo': 'ERROR_LISTAR_PEDIDOS'}, 500)

