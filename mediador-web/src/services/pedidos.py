import os
import requests
from flask import current_app

class PedidoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de pedidos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def listar_pedidos(vendedor_id=None, cliente_id=None, headers=None):
    """
    Obtiene la lista de pedidos del microservicio externo.

    Args:
        vendedor_id (str, optional): Filtro por ID de vendedor.
        cliente_id (str, optional): Filtro por ID de cliente.
        headers (dict, optional): Encabezados HTTP adicionales para la petición.

    Returns:
        dict: Lista de pedidos.

    Raises:
        PedidoServiceError: Si ocurre un error de conexión o del microservicio.
    """
    pedidos_url = os.environ.get('PEDIDOS_URL', 'http://localhost:5012')
    
    # Construir parámetros de consulta
    params = {}
    if vendedor_id:
        params['vendedor_id'] = vendedor_id
    if cliente_id:
        params['cliente_id'] = cliente_id
    
    # Preparar encabezados
    request_headers = {'Content-Type': 'application/json'}
    if headers:
        request_headers.update(headers)
    
    try:
        response = requests.get(
            f"{pedidos_url}/pedido",
            params=params,
            headers=request_headers,
            timeout=10
        )
        response.raise_for_status()
        
        current_app.logger.info(f"Pedidos listados exitosamente")
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de pedidos: {e.response.text}")
        try:
            error_data = e.response.json()
        except Exception:
            error_data = {'error': 'Error del microservicio de pedidos', 'codigo': 'ERROR_HTTP'}
        raise PedidoServiceError(error_data, e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de pedidos: {str(e)}")
        raise PedidoServiceError({
            'error': 'Error de conexión con el microservicio de pedidos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado listando pedidos: {str(e)}")
        raise PedidoServiceError({
            'error': 'Error interno al listar pedidos',
            'codigo': 'ERROR_INESPERADO'
        }, 500)

