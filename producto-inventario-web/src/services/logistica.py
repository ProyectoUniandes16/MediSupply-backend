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


def listar_bodegas() -> dict:
    """
    Obtiene la lista de todas las bodegas disponibles.
    
    Returns:
        dict: Diccionario con 'data' (lista de bodegas) y 'total' (cantidad)
        
    Raises:
        LogisticaServiceError: Si hay error al consultar el servicio
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.get(
            f"{logistica_url}/bodega",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise LogisticaServiceError(
                f"Error al obtener las bodegas: {response.text}",
                response.status_code
            )
            
    except requests.exceptions.RequestException as e:
        raise LogisticaServiceError(
            f"Error de conexión con el servicio de logística: {str(e)}",
            500
        )


def listar_zonas_con_bodegas() -> dict:
    """
    Obtiene la lista de todas las zonas con sus bodegas asociadas.
    
    Returns:
        dict: Diccionario con 'data' (lista de zonas con bodegas) y 'total' (cantidad)
        
    Raises:
        LogisticaServiceError: Si hay error al consultar el servicio
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.get(
            f"{logistica_url}/zona-con-bodegas",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise LogisticaServiceError(
                f"Error al obtener las zonas con bodegas: {response.text}",
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
            ruta_creada = response.json()
            # Actualizar estado de pedidos a "en_proceso"
            _actualizar_estados_pedidos(data.get('ruta', []))
            return ruta_creada
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


def _actualizar_estados_pedidos(ruta: list):
    """
    Actualiza el estado de los pedidos en la ruta a "en_proceso".
    
    Args:
        ruta (list): Lista de puntos de entrega con pedido_id
    """
    pedidos_url = Config.PEDIDOS_URL
    for punto in ruta:
        pedido_id = punto.get('pedido_id')
        if pedido_id:
            try:
                response = requests.patch(
                    f"{pedidos_url}/pedido/{pedido_id}/estado",
                    json={'estado': 'en_proceso'},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if response.status_code != 200:
                    # Log error but don't fail the whole operation
                    print(f"Error al actualizar estado del pedido {pedido_id}: {response.text}")
            except requests.exceptions.RequestException as e:
                # Log error but don't fail
                print(f"Error de conexión al actualizar pedido {pedido_id}: {str(e)}")


def listar_rutas_logistica(filtros=None) -> dict:
    """
    Obtiene la lista de rutas desde el microservicio de logística.
    
    Args:
        filtros (dict, optional): Diccionario con filtros opcionales:
            - estado: Estado de la ruta
            - zona_id: ID de la zona
            - camion_id: ID del camión
            - bodega_id: ID de la bodega
    
    Returns:
        dict: Diccionario con 'data' (lista de rutas) y 'total'
        
    Raises:
        LogisticaServiceError: Si hay error al consultar el servicio
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        # Construir query params
        params = {}
        if filtros:
            if filtros.get('estado'):
                params['estado'] = filtros['estado']
            if filtros.get('zona_id'):
                params['zona_id'] = filtros['zona_id']
            if filtros.get('camion_id'):
                params['camion_id'] = filtros['camion_id']
            if filtros.get('bodega_id'):
                params['bodega_id'] = filtros['bodega_id']
        
        response = requests.get(
            f"{logistica_url}/rutas",
            params=params,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise LogisticaServiceError(
                f"Error al obtener las rutas: {response.text}",
                response.status_code
            )
            
    except requests.exceptions.RequestException as e:
        raise LogisticaServiceError(
            f"Error de conexión con el servicio de logística: {str(e)}",
            500
        )


def obtener_ruta_detallada(ruta_id: str) -> dict:
    """
    Obtiene el detalle completo de una ruta específica.
    
    Args:
        ruta_id (str): ID de la ruta a consultar
        
    Returns:
        dict: Ruta con sus detalles ordenados
        
    Raises:
        LogisticaServiceError: Si hay error al consultar el servicio o la ruta no existe
    """
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.get(
            f"{logistica_url}/rutas/{ruta_id}",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise LogisticaServiceError(
                "Ruta no encontrada",
                404
            )
        else:
            raise LogisticaServiceError(
                f"Error al obtener la ruta: {response.text}",
                response.status_code
            )
            
    except requests.exceptions.RequestException as e:
        raise LogisticaServiceError(
            f"Error de conexión con el servicio de logística: {str(e)}",
            500
        )


def optimizar_ruta(
    payload: dict,
    formato: str = "json",
) -> dict:
    """
    Invoca el microservicio de logística para optimizar una ruta de entrega.
    
    Args:
        payload: Diccionario con 'bodega' (coordenadas) y 'destinos' (lista de coordenadas)
        formato: 'json' o 'html' (por defecto 'json')
        
    Returns:
        Diccionario con la ruta optimizada o HTML del mapa según el formato
    """
    if not isinstance(payload, dict) or not payload:
        raise LogisticaServiceError(
            {"error": "No se proporcionaron datos", "codigo": "DATOS_VACIOS"},
            400,
        )
    
    if not payload.get("bodega"):
        raise LogisticaServiceError(
            {"error": "Campo 'bodega' es requerido", "codigo": "BODEGA_REQUERIDA"},
            400,
        )
    
    if not payload.get("destinos"):
        raise LogisticaServiceError(
            {"error": "Campo 'destinos' es requerido", "codigo": "DESTINOS_REQUERIDOS"},
            400,
        )
    
    logistica_url = Config.LOGISTICA_URL
    
    try:
        response = requests.post(
            f"{logistica_url}/ruta-optima",
            json=payload,
            params={"formato": formato},
            headers={"Content-Type": "application/json"},
            timeout=30,  # Mayor timeout por el procesamiento de rutas
        )
        response.raise_for_status()
        
        # Si el formato es HTML, retornar el texto directamente
        if formato == "html":
            return response.text
        
        # Para JSON, parsear la respuesta
        try:
            return response.json()
        except ValueError:
            raise LogisticaServiceError(
                {
                    "error": "Respuesta inválida del microservicio de logística",
                    "codigo": "RESPUESTA_INVALIDA",
                },
                502,
            )
    
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else 500
        detalle = exc.response.text if exc.response else str(exc)
        raise LogisticaServiceError(
            {
                "error": f"Error HTTP del microservicio de logística: {detalle}",
                "codigo": "ERROR_HTTP",
            },
            status_code,
        )
    
    except requests.exceptions.Timeout:
        raise LogisticaServiceError(
            {
                "error": "Timeout al procesar la optimización de ruta",
                "codigo": "TIMEOUT",
            },
            504,
        )
    
    except requests.exceptions.RequestException as exc:
        raise LogisticaServiceError(
            {
                "error": "Error de conexión con el microservicio de logística",
                "codigo": "ERROR_CONEXION",
            },
            503,
        )
    
    except LogisticaServiceError:
        raise
    
    except Exception as exc:
        raise LogisticaServiceError(
            {
                "error": "Error interno al optimizar ruta",
                "codigo": "ERROR_INESPERADO",
            },
            500,
        )
