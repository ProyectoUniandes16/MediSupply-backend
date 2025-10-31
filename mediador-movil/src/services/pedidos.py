from flask import current_app
import requests
from src.config.config import Config
from src.services.vendedores import listar_vendedores_externo


class PedidoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de pedidos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_pedido_externo(datos_pedido, vendedor_email):
    """
    Lógica de negocio para crear un pedido a través del microservicio externo.

    Args:
        datos_pedido (dict): Datos del pedido a crear.
        cliente_email (str): Email del cliente que realiza el pedido.

    Returns:
        dict: Los datos del pedido creado.
    Raises:
        PedidoServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_pedido:
        raise PedidoServiceError({'error': 'No se proporcionaron datos', 'codigo': 'DATOS_VACIOS'}, 400)

    # --- Validación de datos de entrada ---
    required_fields = ['productos', 'total', 'cliente_id']
    missing_fields = [field for field in required_fields if not datos_pedido.get(field)]
    if missing_fields:
        raise PedidoServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    if not isinstance(datos_pedido['productos'], list) or len(datos_pedido['productos']) == 0:
        raise PedidoServiceError({'error': 'La lista de productos no es válida o está vacía', 'codigo': 'PRODUCTOS_INVALIDOS'}, 400)

    # --- Fin de la validación ---
    pedidos_url = Config.PEDIDOS_URL
    current_app.logger.info(f"URL del microservicio de pedidos: {pedidos_url}")
    try:

        venndedor_response = listar_vendedores_externo(filters={'correo': vendedor_email})

        if not venndedor_response.get('items') or len(venndedor_response['items']) == 0:
            raise PedidoServiceError({'error': 'Vendedor no encontrado', 'codigo': 'VENDEDOR_NO_ENCONTRADO'}, 404)

        vendedor_id = venndedor_response['items'][0]['id']


        response = requests.post(
            pedidos_url+'/pedido',
            json={
                'vendedor_id': vendedor_id,
                **datos_pedido
            },
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx

        current_app.logger.info(f"Pedido creado exitosamente: {response.json()}")
        return response.json()

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error al conectar con el microservicio de pedidos: {str(e)}")
        raise PedidoServiceError({'error': 'Error al conectar con el microservicio de pedidos'}, 503)