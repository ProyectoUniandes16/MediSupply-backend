import json
import os
import requests
from flask import current_app
from src.services.auth import register_user, AuthServiceError
from src.config.config import Config
from src.services.vendedores import obtener_clientes_de_vendedor, VendedorServiceError

class ClienteServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de clientes."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_cliente_externo(datos_cliente):
    """
    Lógica de negocio para crear un cliente a través del microservicio externo.

    Args:
        datos_cliente (dict): Datos del cliente a crear.

    Returns:
        dict: Los datos del cliente creado.

    Raises:
        ClienteServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_cliente:
        raise ClienteServiceError({'error': 'No se proporcionaron datos', 'codigo': 'DATOS_VACIOS'}, 400)

    # --- Validación de datos de entrada ---
    required_fields = ['nombre', 'tipo', 'zona', 'nit', 'nombre_contacto', 'correo_contacto', 'telefono_contacto', 'direccion', 'cargo_contacto', 'correo_empresa']
    missing_fields = [field for field in required_fields if not datos_cliente.get(field)]
    if missing_fields:
        raise ClienteServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    # --- Fin de la validación ---

    clientes_url = Config.CLIENTES_URL
    current_app.logger.info(f"URL del microservicio de clientes: {clientes_url}")
    try:
        response = requests.post(
            clientes_url + '/cliente',
            json=datos_cliente,
            headers={'Content-Type': 'application/json'}
        )

        # Usar raise_for_status para respetar el comportamiento esperado por los tests/mocks
        response.raise_for_status()

        cliente_data = response.json()
        current_app.logger.info(f"Cliente creado exitosamente: {cliente_data}")
        
        return cliente_data
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de clientes: {e.response.text}")
        raise ClienteServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de clientes: {str(e)}")
        raise ClienteServiceError({
            'error': 'Error de conexión con el microservicio de clientes',
            'codigo': 'ERROR_CONEXION'
        }, 503)

def listar_clientes_vendedor_externo(vendedor_email):
    """
    Lógica de negocio para listar clientes a través del microservicio externo.

    Args:
        filtros (dict, optional): Filtros para la consulta de clientes.
        vendedor_email (str, optional): Email del vendedor para filtrar clientes.

    Returns:
        dict: Respuesta del microservicio de clientes.
    """
    try:
        clientes_url = Config.CLIENTES_URL
        vendedores_response = obtener_clientes_de_vendedor(vendedor_email)
        clientes_ids = [item['cliente_id'] for item in vendedores_response['data']]
        print(clientes_ids)
        if not clientes_ids:
            return {
                'data': []
            }
        response = requests.get(
            f"{clientes_url}/cliente?ids={','.join(str(cliente_id) for cliente_id in clientes_ids)}",
            params={
                'vendedor_id': vendedor_email
            },
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
    except VendedorServiceError as e:
        current_app.logger.error(f"Error al obtener clientes del vendedor: {str(e)}")
        raise ClienteServiceError({
            'error': 'Error al obtener clientes del vendedor',
            'codigo': 'ERROR_VENDEDOR'
        }, e.status_code)
