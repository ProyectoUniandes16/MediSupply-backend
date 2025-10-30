import os
import requests
import json
from flask import current_app, jsonify
from src.config.config import Config as config

class ProductoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de productos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def consultar_productos_externo(params=None):
    """
    Consulta productos desde el microservicio externo.

    Args:
        params (dict, optional): Parámetros de consulta.

    Returns:
        dict: Datos de los productos consultados.

    Raises:
        ProductoServiceError: Si ocurre un error de conexión o del microservicio.
    """
    url_producto = config.PRODUCTO_URL + '/api/productos/'

    try:
        response = requests.get(
            url_producto,
            params=params
        )

        # raise_for_status normalmente lanzaría HTTPError para 4xx/5xx.
        # Si eso ocurre será capturado por la excepción de requests y convertido
        # en un ProductoServiceError con código de conexión. Si por alguna razón
        # raise_for_status no lanza, comprobamos el status y levantamos
        # ProductoServiceError con el body y status del backend.
        response.raise_for_status()
        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            raise ProductoServiceError(response.json(), response.status_code)
        return response.json()
    except ProductoServiceError:
        # Si ya estamos lanzando un ProductoServiceError (por ejemplo porque el
        # backend devolvió un body con detalles) lo re-lanzamos tal cual para
        # que el caller pueda manejarlo (no lo convertimos en ERROR_CONEXION).
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        # Capturar cualquier otro error inesperado y exponer un error de conexión genérico.
        current_app.logger.error(f"Error inesperado consultando microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)


def obtener_detalle_producto_externo(producto_id):
    """
    Obtiene el detalle completo de un producto por ID desde el microservicio.

    Args:
        producto_id (int): ID del producto a consultar.

    Returns:
        dict: Detalle completo del producto incluyendo stock y certificaciones.

    Raises:
        ProductoServiceError: Si el producto no existe o hay error de conexión.
    """
    url_producto = f"{config.PRODUCTO_URL}/api/productos/{producto_id}"

    try:
        response = requests.get(url_producto)

        if response.status_code == 404:
            current_app.logger.warning(f"Producto {producto_id} no encontrado")
            raise ProductoServiceError({
                'error': f'Producto con ID {producto_id} no encontrado',
                'codigo': 'PRODUCTO_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle de producto: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al obtener detalle del producto',
            'codigo': 'ERROR_INESPERADO'
        }, 500)


def obtener_producto_por_sku_externo(sku):
    """
    Obtiene el detalle de un producto por código SKU desde el microservicio.

    Args:
        sku (str): Código SKU del producto.

    Returns:
        dict: Detalle completo del producto.

    Raises:
        ProductoServiceError: Si el SKU no existe o hay error de conexión.
    """
    if not sku or not sku.strip():
        raise ProductoServiceError({
            'error': 'El código SKU es requerido',
            'codigo': 'SKU_REQUERIDO'
        }, 400)

    url_producto = f"{config.PRODUCTO_URL}/api/productos/sku/{sku}"

    try:
        response = requests.get(url_producto)

        if response.status_code == 404:
            current_app.logger.warning(f"Producto con SKU {sku} no encontrado")
            raise ProductoServiceError({
                'error': f'Producto con SKU {sku} no encontrado',
                'codigo': 'PRODUCTO_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo producto por SKU: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al obtener producto por SKU',
            'codigo': 'ERROR_INESPERADO'
        }, 500)