import requests

from src.config.config import Config


class LogisticaServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de logística."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def listar_zonas() -> dict:
    """
    Obtiene la lista de todas las zonas disponibles.
    
    Returns:
        dict: Diccionario con 'data' (lista de zonas) y 'total' (cantidad)
        
    Raises:
        LogisticaServiceError: Si hay error al consultar el servicio
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.get(
            f"{logistica_url}/zona",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise LogisticaServiceError(
                f"Error al obtener las zonas: {response.text}",
                response.status_code
            )
            
    except requests.exceptions.RequestException as e:
        raise LogisticaServiceError(
            f"Error de conexión con el servicio de logística: {str(e)}",
            500
        )


def obtener_zona_detallada(zona_id: str) -> dict:
    """
    Obtiene el detalle completo de una zona incluyendo sus bodegas y camiones.
    
    Args:
        zona_id (str): ID de la zona a consultar
        
    Returns:
        dict: Zona con sus bodegas y los camiones de cada bodega
        
    Raises:
        LogisticaServiceError: Si hay error al consultar el servicio o la zona no existe
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.get(
            f"{logistica_url}/zona/{zona_id}/detalle",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise LogisticaServiceError(
                "Zona no encontrada",
                404
            )
        else:
            raise LogisticaServiceError(
                f"Error al obtener el detalle de la zona: {response.text}",
                response.status_code
            )
            
    except requests.exceptions.RequestException as e:
        raise LogisticaServiceError(
            f"Error de conexión con el servicio de logística: {str(e)}",
            500
        )


def crear_ruta_entrega(data: dict) -> dict:
    """
    Crea una nueva ruta de entrega en el servicio de logística.
    
    Args:
        data (dict): Datos de la ruta a crear con los campos:
            - bodega_id (str): ID de la bodega de origen
            - camion_id (str): ID del camión asignado
            - zona_id (str): ID de la zona de entrega
            - estado (str): Estado inicial de la ruta (pendiente, iniciado, en_progreso, etc.)
            - ruta (list): Lista de puntos de entrega, cada uno con:
                - ubicacion (list): [longitud, latitud]
                - pedido_id (str): ID del pedido a entregar
    
    Returns:
        dict: Ruta creada con sus detalles
        
    Raises:
        LogisticaServiceError: Si hay error al crear la ruta
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.post(
            f"{logistica_url}/rutas",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 400:
            error_data = response.json()
            raise LogisticaServiceError(
                error_data.get('error', 'Error de validación'),
                400
            )
        elif response.status_code == 404:
            error_data = response.json()
            raise LogisticaServiceError(
                error_data.get('error', 'Recurso no encontrado'),
                404
            )
        else:
            raise LogisticaServiceError(
                f"Error al crear la ruta: {response.text}",
                response.status_code
            )
            
    except requests.exceptions.RequestException as e:
        raise LogisticaServiceError(
            f"Error de conexión con el servicio de logística: {str(e)}",
            500
        )
