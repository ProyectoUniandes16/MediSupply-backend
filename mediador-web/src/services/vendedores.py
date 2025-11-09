import os
import requests
from flask import current_app
from src.services.auth import register_user, AuthServiceError
from src.services.pedidos import obtener_pedidos_vendedor, PedidosServiceError
from datetime import datetime
from decimal import Decimal

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


def generar_reporte_ventas_vendedor(vendedor_id, mes, anio):
    """
    Genera datos agregados para el reporte de ventas de un vendedor.
    Orquesta llamadas a microservicios de vendedores y pedidos.
    
    Args:
        vendedor_id (str): ID del vendedor
        mes (int): Mes (1-12)
        anio (int): Año (ej: 2025)
        
    Returns:
        dict: Datos agregados del reporte con:
            - vendedor: Información del vendedor
            - periodo: Periodo del reporte
            - planes: Lista de planes con métricas calculadas
            - totales: Totales generales
            
    Raises:
        VendedorServiceError: Si ocurre un error al generar el reporte
    """
    try:
        # Validar mes y año
        if not isinstance(mes, int) or mes < 1 or mes > 12:
            raise VendedorServiceError({
                'error': 'El mes debe ser un número entre 1 y 12',
                'codigo': 'MES_INVALIDO'
            }, 400)
        
        if not isinstance(anio, int) or anio < 2020 or anio > 2050:
            raise VendedorServiceError({
                'error': 'El año debe estar entre 2020 y 2050',
                'codigo': 'ANIO_INVALIDO'
            }, 400)
        
        # 1. Obtener información del vendedor
        vendedor = obtener_detalle_vendedor_externo(vendedor_id)
        
        # 2. Construir periodo en formato YYYY-MM
        periodo = f"{anio:04d}-{mes:02d}"
        
        # 3. Obtener planes de venta del vendedor para ese periodo
        planes_response = listar_planes_venta_externo(
            vendedor_id=vendedor_id,
            periodo=periodo,
            page=1,
            size=100  # Asumiendo que un vendedor no tiene más de 100 planes en un mes
        )
        
        planes = planes_response.get('items', [])
        
        # 4. Obtener pedidos del vendedor para ese mes/año
        try:
            pedidos = obtener_pedidos_vendedor(vendedor_id, mes, anio)
        except PedidosServiceError as e:
            current_app.logger.error(f"Error al obtener pedidos: {str(e)}")
            # Si no se pueden obtener pedidos, continuar con datos vacíos
            pedidos = []
        
        # 5. Calcular métricas
        # Agrupar pedidos por estado
        # Incluir todos los pedidos excepto cancelados/rechazados
        pedidos_completados = [p for p in pedidos if p.get('estado') not in ['cancelado', 'rechazado', 'anulado']]
        
        # Clientes únicos
        clientes_unicos = set(p.get('cliente_id') for p in pedidos_completados if p.get('cliente_id'))
        
        # Totales de ventas
        total_ventas = len(pedidos_completados)
        monto_total = sum(float(p.get('total', 0)) for p in pedidos_completados)
        monto_promedio = monto_total / total_ventas if total_ventas > 0 else 0
        
        # 6. Calcular métricas por plan y totales generales
        planes_con_metricas = []
        meta_ingresos_total = Decimal('0')
        
        for plan in planes:
            meta_ingresos = Decimal(str(plan.get('meta_ingresos', 0)))
            meta_ingresos_total += meta_ingresos
            
            # Calcular cumplimiento
            cumplimiento = (Decimal(str(monto_total)) / meta_ingresos * 100) if meta_ingresos > 0 else Decimal('0')
            
            planes_con_metricas.append({
                'nombre_plan': plan.get('nombre_plan', 'Sin nombre'),
                'periodo': plan.get('periodo', periodo),
                'meta_ingresos': float(meta_ingresos),
                'meta_visitas': plan.get('meta_visitas', 0),
                'meta_clientes_nuevos': plan.get('meta_clientes_nuevos', 0),
            })
        
        # Si el vendedor tiene múltiples planes, el cumplimiento es sobre la suma de metas
        cumplimiento_total = (Decimal(str(monto_total)) / meta_ingresos_total * 100) if meta_ingresos_total > 0 else Decimal('0')
        
        return {
            'vendedor': {
                'id': vendedor.get('id'),
                'nombre_completo': f"{vendedor.get('nombre', '')} {vendedor.get('apellidos', '')}".strip(),
                'correo': vendedor.get('correo'),
                'zona': vendedor.get('zona', 'N/A')
            },
            'periodo': {
                'mes': mes,
                'anio': anio,
                'periodo_formato': periodo,
                'mes_nombre': _obtener_nombre_mes(mes)
            },
            'planes': planes_con_metricas,
            'metricas': {
                'ventas_realizadas': total_ventas,
                'monto_total': round(monto_total, 2),
                'monto_promedio': round(monto_promedio, 2),
                'clientes_unicos': len(clientes_unicos),
                'meta_ingresos_total': float(meta_ingresos_total),
                'cumplimiento_porcentaje': float(round(cumplimiento_total, 2))
            },
            'pedidos_detalle': pedidos_completados  # Para análisis adicional si se necesita
        }
        
    except VendedorServiceError:
        # Re-lanzar errores de vendedor
        raise
    except Exception as e:
        current_app.logger.error(f"Error inesperado al generar reporte: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error interno al generar el reporte de ventas',
            'codigo': 'ERROR_GENERAR_REPORTE',
            'detalle': str(e)
        }, 500)


def _obtener_nombre_mes(mes):
    """Retorna el nombre del mes en español."""
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    return meses.get(mes, 'Desconocido')
   