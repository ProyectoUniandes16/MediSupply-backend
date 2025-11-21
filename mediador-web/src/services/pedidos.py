"""
Servicio para interactuar con el microservicio de pedidos.
"""
import os
import requests
import logging
from flask import current_app
from datetime import datetime


class PedidosServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de pedidos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def obtener_pedidos_vendedor(vendedor_id, mes=None, anio=None):
    """
    Obtiene los pedidos de un vendedor desde el microservicio de pedidos.
    Filtra por mes y año si se proporcionan.
    
    Args:
        vendedor_id (str): ID del vendedor
        mes (int, optional): Mes (1-12) para filtrar
        anio (int, optional): Año para filtrar
        
    Returns:
        list: Lista de pedidos del vendedor (filtrados por fecha si aplica)
        
    Raises:
        PedidosServiceError: Si ocurre un error de conexión o del microservicio
    """
    pedidos_url = os.environ.get('PEDIDOS_URL', 'http://localhost:5012')
    
    def _safe_log_error(msg):
        """Loggea un mensaje de error usando current_app si está disponible,
        y en su defecto usa el logger estándar.
        """
        try:
            current_app.logger.error(msg)
        except RuntimeError:
            logging.getLogger(__name__).error(msg)

    def _safe_log_warning(msg):
        try:
            current_app.logger.warning(msg)
        except RuntimeError:
            logging.getLogger(__name__).warning(msg)

    try:
        # Llamar al endpoint de pedidos con filtro de vendedor
        response = requests.get(
            f"{pedidos_url}/pedido",
            params={'vendedor_id': vendedor_id},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        pedidos = data.get('data', [])
        
        # Si se proporcionaron mes y año, filtrar por fecha
        if mes is not None and anio is not None:
            pedidos_filtrados = []
            for pedido in pedidos:
                try:
                    # Parsear la fecha del pedido
                    fecha_str = pedido.get('fecha_pedido')
                    if fecha_str:
                        # Soporta formato ISO: "2025-01-15T10:30:00"
                        fecha_pedido = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                        
                        # Verificar si coincide con mes y año
                        if fecha_pedido.month == mes and fecha_pedido.year == anio:
                            pedidos_filtrados.append(pedido)
                except (ValueError, AttributeError) as e:
                    _safe_log_warning(f"Error al parsear fecha de pedido {pedido.get('id')}: {str(e)}")
                    continue
            
            return pedidos_filtrados
        
        return pedidos
        
    except requests.exceptions.HTTPError as e:
        _safe_log_error(f"Error del microservicio de pedidos: {e.response.text}")
        try:
            error_data = e.response.json()
        except Exception:
            error_data = {'error': e.response.text, 'codigo': 'ERROR_INESPERADO'}
        raise PedidosServiceError(error_data, e.response.status_code)
    except requests.exceptions.RequestException as e:
        _safe_log_error(f"Error de conexión con microservicio de pedidos: {str(e)}")
        raise PedidosServiceError({
            'error': 'Error de conexión con el microservicio de pedidos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        _safe_log_error(f"Error inesperado al obtener pedidos: {str(e)}")
        raise PedidosServiceError({
            'error': 'Error interno al obtener pedidos',
            'codigo': 'ERROR_INESPERADO',
            'detalle': str(e)
        }, 500)

def listar_pedidos(vendedor_id=None, cliente_id=None, zona=None, headers=None):
    """
    Obtiene la lista de pedidos del microservicio externo.
    Si se especifica zona, filtra los pedidos por la zona del cliente.

    Args:
        vendedor_id (str, optional): Filtro por ID de vendedor.
        cliente_id (str, optional): Filtro por ID de cliente.
        zona (str, optional): Filtro por zona del cliente.
        headers (dict, optional): Encabezados HTTP adicionales para la petición.

    Returns:
        dict: Lista de pedidos filtrados.

    Raises:
        PedidosServiceError: Si ocurre un error de conexión o del microservicio.
    """
    pedidos_url = os.environ.get('PEDIDOS_URL', 'http://localhost:5012')
    clientes_url = os.environ.get('CLIENTES_URL', 'http://localhost:5010')
    
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
        # Obtener pedidos del microservicio
        response = requests.get(
            f"{pedidos_url}/pedido",
            params=params,
            headers=request_headers,
            timeout=10
        )
        response.raise_for_status()
        
        pedidos_data = response.json()
        
        # Si no se filtra por zona, retornar todos
        if not zona:
            current_app.logger.info(f"Pedidos listados exitosamente")
            return pedidos_data
        
        # Filtrar por zona: para cada pedido, obtener zona del cliente
        pedidos_filtrados = []
        for pedido in pedidos_data.get('data', []):
            try:
                cliente_id_pedido = pedido.get('cliente_id')
                if cliente_id_pedido:
                    # Llamada al microservicio de clientes para obtener zona
                    cliente_response = requests.get(
                        f"{clientes_url}/cliente/{cliente_id_pedido}",
                        headers=request_headers,
                        timeout=5
                    )
                    cliente_response.raise_for_status()
                    cliente_data = cliente_response.json()
                    
                    # Verificar zona
                    zona_cliente = cliente_data.get('data', {}).get('zona')
                    if zona_cliente == zona:
                        pedidos_filtrados.append(pedido)
            except requests.exceptions.RequestException as e:
                current_app.logger.warning(f"Error obteniendo zona para cliente {cliente_id_pedido}: {str(e)}")
                continue  # Saltar este pedido si falla la obtención de zona
        
        current_app.logger.info(f"Pedidos filtrados por zona '{zona}': {len(pedidos_filtrados)} encontrados")
        return {'data': pedidos_filtrados}
        
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de pedidos: {e.response.text}")
        try:
            error_data = e.response.json()
        except Exception:
            error_data = {'error': 'Error del microservicio de pedidos', 'codigo': 'ERROR_HTTP'}
        raise PedidosServiceError(error_data, e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de pedidos: {str(e)}")
        raise PedidosServiceError({
            'error': 'Error de conexión con el microservicio de pedidos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado listando pedidos: {str(e)}")
        raise PedidosServiceError({
            'error': 'Error interno al listar pedidos',
            'codigo': 'ERROR_INESPERADO'
        }, 500)

