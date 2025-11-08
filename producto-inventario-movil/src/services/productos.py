from venv import logger
import requests
import json
from flask import current_app, jsonify
from src.config.config import Config as config
from typing import Any, Dict, Iterable, List, MutableMapping, Optional
from src.services.inventarios import InventarioServiceError, _get_inventarios_by_producto, _actualizar_inventario, obtener_productos_con_inventarios

class ProductoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de productos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def get_productos_con_inventarios(params: Optional[MutableMapping[str, Any]] = None) -> Dict[str, Any]:
    """Obtiene los productos y enriquece con inventarios usando cache por producto."""
    try:
        productos_payload = consultar_productos_externo(params)
    except ProductoServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        logger.error("Error inesperado consultando microservicio de productos: %s", exc)
        raise ProductoServiceError({
            'error': 'Error inesperado consultando productos',
            'codigo': 'ERROR_INESPERADO'
        }, 500) from exc

    productos = _extract_productos(productos_payload)

    inventario_response = obtener_productos_con_inventarios(productos)

    if isinstance(productos_payload, MutableMapping):
        inventario_response['meta'] = {
            key: productos_payload[key]
            for key in ('total', 'limit', 'offset', 'count')
            if key in productos_payload
        }

    return inventario_response
    

def _extract_productos(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, MutableMapping):
        for key in ('data', 'productos', 'items', 'results'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []

def aplanar_productos_con_inventarios(data: Dict[str, Any]):
    """Aplana la estructura de productos con inventarios para sólo retornar productos."""
    productos = data.get('data', [])
    resultado = []
    for producto in productos:
        if not isinstance(producto, MutableMapping):
            continue
        prod_copy = producto.copy()
        # Remover campos de inventario
        prod_copy.pop('inventarios', None)
        prod_copy['cantidad_disponible'] = prod_copy.pop('totalInventario', 0)
        resultado.append(prod_copy)
    return {
        'data': resultado,
        'source': data.get('source', 'unknown')
    }

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
        
        producto = response.json()

        try:
            inventarios = _get_inventarios_by_producto(producto_id)
            producto["producto"]['inventarios'] = inventarios["data"]["inventarios"]
        except Exception:
            producto['inventario'] = []
            current_app.logger.error(f"No se pudieron obtener inventarios para el producto {producto_id}")

        # Eliminar posibles claves 'inventario' tanto en el root como dentro
        # del objeto anidado 'producto' para normalizar la respuesta.
        producto.pop('inventario', None)
        if isinstance(producto.get('producto'), MutableMapping):
            producto['producto'].pop('inventario', None)

        return producto

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


def subir_video_producto_externo(producto_id, video_file, descripcion, usuario_registro):
    """
    Sube un video de evidencia para un producto al microservicio de productos.

    Args:
        producto_id (int): ID del producto.
        video_file: Archivo de video (FileStorage).
        descripcion (str): Descripción del video.
        usuario_registro (str): Usuario que sube el video.

    Returns:
        dict: Respuesta del microservicio con datos del video subido.

    Raises:
        ProductoServiceError: Si hay error en la validación o subida.
    """
    url_video = f"{config.PRODUCTO_URL}/api/productos/{producto_id}/videos"

    try:
        # Preparar los datos del formulario
        files = {
            'video': (video_file.filename, video_file.stream, video_file.content_type)
        }
        
        data = {
            'descripcion': descripcion,
            'usuario_registro': usuario_registro
        }

        current_app.logger.info(f"Subiendo video para producto {producto_id}")
        
        # Realizar la petición POST con multipart/form-data
        response = requests.post(
            url_video,
            files=files,
            data=data,
            timeout=300  # 5 minutos de timeout para videos grandes
        )

        if response.status_code == 404:
            current_app.logger.warning(f"Producto {producto_id} no encontrado")
            raise ProductoServiceError({
                'error': f'Producto con ID {producto_id} no encontrado',
                'codigo': 'PRODUCTO_NO_ENCONTRADO'
            }, 404)

        if response.status_code == 400:
            current_app.logger.warning(f"Validación fallida al subir video: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': 'Datos inválidos', 'codigo': 'DATOS_INVALIDOS'}
            raise ProductoServiceError(error_data, 400)

        if response.status_code == 413:
            current_app.logger.warning(f"Video muy grande para producto {producto_id}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {
                    'error': 'El archivo supera el tamaño máximo permitido (150 MB)',
                    'codigo': 'ARCHIVO_MUY_GRANDE'
                }
            raise ProductoServiceError(error_data, 413)

        if response.status_code != 201:
            current_app.logger.error(f"Error del microservicio al subir video: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.Timeout as e:
        current_app.logger.error(f"Timeout subiendo video para producto {producto_id}: {str(e)}")
        raise ProductoServiceError({
            'error': 'El tiempo de espera para subir el video se agotó. Intenta con un archivo más pequeño.',
            'codigo': 'TIMEOUT'
        }, 504)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión subiendo video: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado subiendo video: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al subir el video',
            'codigo': 'ERROR_INESPERADO'
        }, 500)