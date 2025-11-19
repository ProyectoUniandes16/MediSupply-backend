import json
import os
import requests
from flask import current_app
from src.config.config import Config
from src.services.vendedores import obtener_clientes_de_vendedor, VendedorServiceError

class ClienteServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de clientes."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def listar_clientes_externo(email):
    """
    Lógica de negocio para listar clientes a través del microservicio externo.

    Args:
        cliente_id (str): ID del cliente para filtrar clientes.

    Returns:
        dict: Respuesta del microservicio de clientes.
    """
    try:
        clientes_url = Config.CLIENTES_URL
        response = requests.get(
            f"{clientes_url}/cliente?correo_empresa={email}",
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de clientes: {e.response.text}")
        raise ClienteServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de clientes: {str(e)}")
        raise ClienteServiceError({
            'error': 'Error de conexión con el microservicio de clientes',
            'codigo': 'ERROR_CONEXION'
        }, 503)
