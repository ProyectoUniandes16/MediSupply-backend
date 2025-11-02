import os
import requests
from flask import current_app
from src.services.auth import register_user, AuthServiceError

class VendedorServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de vendedores."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_vendedor_externo(datos_vendedor):
    """
    Lógica de negocio para crear un vendedor a través del microservicio externo.

    Args:
        datos_vendedor (dict): Datos del vendedor a crear.

    Returns:
        dict: Los datos del vendedor creado.

    Raises:
        VendedorServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_vendedor:
        raise VendedorServiceError({'error': 'No se proporcionaron datos'}, 400)

    # --- Validación de datos de entrada ---
    required_fields = ['nombre', 'apellidos', 'correo', 'telefono']
    missing_fields = [field for field in required_fields if not datos_vendedor.get(field)]
    if missing_fields:
        raise VendedorServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    # --- Fin de la validación ---

    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    try:
        response = requests.post(
            f"{vendedores_url}/v1/vendedores",
            json=datos_vendedor,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx

        current_app.logger.info(f"Vendedor creado exitosamente: {response.json()}")
    
        try:
            datos_signup_vendedor = {
                'email': datos_vendedor['correo'],
                'password': 'defaultPassword123',  # Contraseña por defecto o generada
                'nombre': datos_vendedor['nombre'],
                'apellido': datos_vendedor['apellidos'],
                'rol': 'vendedor'
            }

            registro_response = register_user(datos_signup_vendedor)
            current_app.logger.info(f"Usuario de vendedor registrado exitosamente: {registro_response}")

            datos_respuesta = response.json()
        except AuthServiceError as e:
            print(f"Error al crear la cuenta de usuario de vendedor: {e.message} el registro del vendedor fue exitoso.")
        return datos_respuesta
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        raise VendedorServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)

def listar_vendedores(zona=None, estado=None, page=1, size=10):
    """
    Obtiene la lista de vendedores del microservicio externo.

    Args:
        zona (str, optional): Filtro por zona.
        estado (str, optional): Filtro por estado.
        page (int): Número de página (default: 1).
        size (int): Tamaño de página (default: 10).

    Returns:
        dict: Lista paginada de vendedores.

    Raises:
        VendedorServiceError: Si ocurre un error de conexión o del microservicio.
    """
    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    
    # Construir parámetros de consulta
    params = {
        'page': page,
        'size': size
    }
    if zona:
        params['zona'] = zona
    if estado:
        params['estado'] = estado
    
    try:
        response = requests.get(
            f"{vendedores_url}/v1/vendedores",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        current_app.logger.info(f"Vendedores listados exitosamente: página {page}")
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        raise VendedorServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)

def obtener_detalle_vendedor_externo(vendedor_id):
    """
    Obtiene el detalle completo de un vendedor por ID desde el microservicio.

    Args:
        vendedor_id (int): ID del vendedor a consultar.

    Returns:
        dict: Detalle completo del vendedor.

    Raises:
        VendedorServiceError: Si el vendedor no existe o hay error de conexión.
    """
    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    try:
        response = requests.get(f"{vendedores_url}/v1/vendedores/{vendedor_id}")
        response.raise_for_status()
        
        if response.status_code == 404:
            current_app.logger.warning(f"Vendedor {vendedor_id} no encontrado")
            raise VendedorServiceError({
                'error': f'Vendedor con ID {vendedor_id} no encontrado',
                'codigo': 'VENDEDOR_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de vendedores: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise VendedorServiceError(error_data, response.status_code)

        return response.json()
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        raise VendedorServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle de vendedor: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error interno al obtener detalle del vendedor',
            'codigo': 'ERROR_INESPERADO'
        }, 500)


def crear_plan_venta_externo(datos_plan):
    """
    Crea un plan de venta a través del microservicio de vendedores.

    Args:
        datos_plan (dict): Datos del plan de venta a crear:
            - nombre_plan (str): Nombre del plan
            - gerente_id (str): ID del gerente comercial
            - vendedores_ids (list): Lista de IDs de vendedores
            - periodo (str): Periodo YYYY-MM
            - meta_ingresos (decimal): Objetivo de ingresos
            - meta_visitas (int): Objetivo de visitas
            - meta_clientes_nuevos (int): Objetivo de clientes nuevos
            - estado (str, opcional): Estado del plan

    Returns:
        dict: Los datos del plan de venta creado.

    Raises:
        VendedorServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_plan:
        raise VendedorServiceError({'error': 'No se proporcionaron datos'}, 400)

    # Validación de campos obligatorios
    required_fields = ['nombre_plan', 'gerente_id', 'vendedores_ids', 'periodo', 
                      'meta_ingresos', 'meta_visitas', 'meta_clientes_nuevos']
    missing_fields = [field for field in required_fields if field not in datos_plan]
    if missing_fields:
        raise VendedorServiceError({
            'error': f"Campos faltantes: {', '.join(missing_fields)}",
            'codigo': 'CAMPOS_FALTANTES'
        }, 400)

    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    try:
        response = requests.post(
            f"{vendedores_url}/v1/planes-venta",
            json=datos_plan,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()

        current_app.logger.info(f"Plan de venta creado exitosamente: {response.json()}")
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        try:
            error_data = e.response.json()
        except Exception:
            error_data = {'error': e.response.text, 'codigo': 'ERROR_INESPERADO'}
        raise VendedorServiceError(error_data, e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)


def listar_planes_venta_externo(vendedor_id=None, periodo=None, estado=None, nombre_plan=None, page=1, size=10):
    """
    Obtiene la lista de planes de venta del microservicio externo.

    Args:
        vendedor_id (str, optional): Filtro por vendedor.
        periodo (str, optional): Filtro por periodo (YYYY-MM).
        estado (str, optional): Filtro por estado.
        nombre_plan (str, optional): Filtro por nombre del plan (búsqueda parcial).
        page (int): Número de página (default: 1).
        size (int): Tamaño de página (default: 10).

    Returns:
        dict: Lista paginada de planes de venta.

    Raises:
        VendedorServiceError: Si ocurre un error de conexión o del microservicio.
    """
    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    
    # Construir parámetros de consulta
    params = {
        'page': page,
        'size': size
    }
    if vendedor_id:
        params['vendedor_id'] = vendedor_id
    if periodo:
        params['periodo'] = periodo
    if estado:
        params['estado'] = estado
    if nombre_plan:
        params['nombre_plan'] = nombre_plan
    
    try:
        response = requests.get(
            f"{vendedores_url}/v1/planes-venta",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        current_app.logger.info(f"Planes de venta listados exitosamente: página {page}")
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        try:
            error_data = e.response.json()
        except Exception:
            error_data = {'error': e.response.text, 'codigo': 'ERROR_INESPERADO'}
        raise VendedorServiceError(error_data, e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)


def obtener_plan_venta_externo(plan_id):
    """
    Obtiene el detalle completo de un plan de venta por ID desde el microservicio.

    Args:
        plan_id (str): ID del plan de venta a consultar.

    Returns:
        dict: Detalle completo del plan de venta.

    Raises:
        VendedorServiceError: Si el plan no existe o hay error de conexión.
    """
    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007')
    try:
        response = requests.get(f"{vendedores_url}/v1/planes-venta/{plan_id}")
        response.raise_for_status()
        
        if response.status_code == 404:
            current_app.logger.warning(f"Plan de venta {plan_id} no encontrado")
            raise VendedorServiceError({
                'error': f'Plan de venta con ID {plan_id} no encontrado',
                'codigo': 'PLAN_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de vendedores: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise VendedorServiceError(error_data, response.status_code)

        return response.json()
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        try:
            error_data = e.response.json()
        except Exception:
            error_data = {'error': e.response.text, 'codigo': 'ERROR_INESPERADO'}
        raise VendedorServiceError(error_data, e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle del plan de venta: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error interno al obtener detalle del plan de venta',
            'codigo': 'ERROR_INESPERADO'
        }, 500)
   