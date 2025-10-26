import json
import os
import requests
from flask import current_app
from src.services.auth import register_user, AuthServiceError
from src.config.config import Config

class ClienteServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de clientes."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_cliente_externo(datos_cliente, vendedor_email):
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
    required_fields = ['nombre', 'tipo', 'pais', 'nit', 'nombre_contacto', 'correo_contacto', 'telefono_contacto', 'direccion', 'cargo_contacto', 'correo_empresa']
    missing_fields = [field for field in required_fields if not datos_cliente.get(field)]
    if missing_fields:
        raise ClienteServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    # --- Fin de la validación ---

    clientes_url = Config.CLIENTES_URL
    current_app.logger.info(f"URL del microservicio de clientes: {clientes_url}")
    try:
        response = requests.post(
            clientes_url+'/cliente',
            json=datos_cliente,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx

        current_app.logger.info(f"Cliente creado exitosamente: {response.json()}")
        cliente_response = response.json()
    
        try:
            datos_signup_cliente = {
                'email': datos_cliente['correo_empresa'],
                'password': 'defaultPassword123',  # Contraseña por defecto o generada
                'nombre': datos_cliente['nombre'],
                'apellido': "",
                'rol': 'cliente'
            }

            registro_response = register_user(datos_signup_cliente)
            current_app.logger.info(f"Usuario de cliente registrado exitosamente: {registro_response}")
            current_app.logger.info(f"Registro response: {registro_response}")
            cliente_id = cliente_response.get('data').get('cliente').get('id')

            # Si no encontramos cliente_id en la respuesta del microservicio de clientes,
            # intentamos obtenerlo del registro de usuario (registro_response)
            if not cliente_id:
                try:
                    cliente_id = registro_response.get('data', {}).get('user', {}).get('id')
                except Exception:
                    cliente_id = None

            current_app.logger.info(f"Cliente registrado (cliente_id={cliente_id}), procediendo a asociar con vendedor...")
            vendedores_url = Config.VENDEDORES_URL
            # Log adicional para depuración: URL usada y payload que se enviará al microservicio de vendedores
            current_app.logger.info(f"VENDEDORES_URL: {vendedores_url}")
            payload_asociacion = {
                'vendedor_email': vendedor_email,
                'cliente_id': cliente_id
            }
            current_app.logger.info(f"Payload para asociar cliente a vendedor: {payload_asociacion}")

            asociar_response = requests.patch(
                url=f'{vendedores_url}/v1/vendedores/clientes',
                json=payload_asociacion,
                headers={'Content-Type': 'application/json'},
            )
            asociar_response.raise_for_status()
            current_app.logger.info(f"Cliente asociado al vendedor exitosamente: {asociar_response.json()}")
        except AuthServiceError as e:
            current_app.logger.info(f"Error al crear la cuenta de usuario de cliente: {e.message} el registro del cliente fue exitoso.")
        except Exception as e:
            current_app.logger.info(f"Error al asociar el cliente al vendedor: {str(e)} el registro del cliente fue exitoso.")
        return cliente_response
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de clientes: {e.response.text}")
        raise ClienteServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de clientes: {str(e)}")
        raise ClienteServiceError({
            'error': 'Error de conexión con el microservicio de clientes',
            'codigo': 'ERROR_CONEXION'
        }, 503)
