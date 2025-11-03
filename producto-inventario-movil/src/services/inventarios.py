"""Servicio para construir la vista de productos con inventarios para el BFF móvil.

Consulta directamente los microservicios de productos e inventarios y utiliza el
Redis Service como cache por producto.
"""
from __future__ import annotations

from calendar import c
import logging
from typing import Any, Dict, Iterable, List, MutableMapping, Optional

import requests
from flask import current_app

from src.services.cache_client import CacheClient
from src.services.productos import ProductoServiceError, consultar_productos_externo

logger = logging.getLogger(__name__)


class InventarioServiceError(Exception):
    """Error de negocio en el servicio de inventarios del BFF móvil."""

    def __init__(self, message: Dict[str, Any], status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _extract_productos(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, MutableMapping):
        for key in ('data', 'productos', 'items', 'results'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _build_cache_payload(inventarios: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    inventarios_list = list(inventarios)
    total_inventario = sum(
        inv.get('cantidad', 0) for inv in inventarios_list if isinstance(inv, MutableMapping)
    )
    return {
        'inventarios': inventarios_list,
        'totalInventario': total_inventario
    }


def _resolve_inventarios_from_cache(
    cache_client: CacheClient,
    producto_id: str
) -> Optional[Dict[str, Any]]:
    cached = cache_client.get_inventarios_by_producto(producto_id)
    if cached is None:
        return None
    if isinstance(cached, MutableMapping):
        # Normalizamos en caso de que sólo se haya almacenado la lista
        inventarios = cached.get('inventarios')
        if isinstance(inventarios, list):
            total = cached.get('totalInventario')
            if not isinstance(total, (int, float)):
                total = sum(inv.get('cantidad', 0) for inv in inventarios if isinstance(inv, MutableMapping))
            return {
                'inventarios': inventarios,
                'totalInventario': total,
                'source': 'cache'
            }
    if isinstance(cached, list):
        payload = _build_cache_payload(cached)
        payload['source'] = 'cache'
        return payload
    logger.warning("Cache para producto %s tiene un formato inesperado", producto_id)
    return None


def _fetch_inventarios_from_upstream(producto_id: str) -> Dict[str, Any]:
    cfg = current_app.config
    base_url = cfg.get('INVENTARIOS_URL', 'http://localhost:5009').rstrip('/')
    timeout = cfg.get('INVENTARIOS_TIMEOUT', 8)

    try:
        response = requests.get(
            f"{base_url}/api/inventarios",
            params={'productoId': producto_id},
            timeout=timeout
        )
    except requests.RequestException as exc:
        logger.error("Error de conexión al microservicio de inventarios: %s", exc)
        raise InventarioServiceError({
            'error': 'Error de conexión con el microservicio de inventarios',
            'codigo': 'ERROR_CONEXION'
        }, 503) from exc

    if response.status_code != 200:
        logger.error(
            "Microservicio de inventarios devolvió %s: %s",
            response.status_code,
            response.text
        )
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {'error': response.text or 'Error inesperado'}
        raise InventarioServiceError(error_payload, response.status_code)

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Respuesta inválida del microservicio de inventarios: %s", exc)
        raise InventarioServiceError({
            'error': 'Respuesta inválida del microservicio de inventarios',
            'codigo': 'RESPUESTA_INVALIDA'
        }, 502) from exc

    if isinstance(data, MutableMapping):
        inventarios = data.get('inventarios', [])
    else:
        inventarios = data

    if not isinstance(inventarios, list):
        logger.warning("Inventarios para producto %s no es una lista", producto_id)
        inventarios = []

    payload = _build_cache_payload(inventarios)
    payload['source'] = 'microservice'
    return payload


def _upsert_cache(cache_client: CacheClient, producto_id: str, payload: Dict[str, Any]) -> None:
    to_cache = {
        'inventarios': payload.get('inventarios', []),
        'totalInventario': payload.get('totalInventario', 0)
    }
    cache_client.set_inventarios_by_producto(producto_id, to_cache)


def get_productos_con_inventarios(params: Optional[MutableMapping[str, Any]] = None) -> Dict[str, Any]:
    """Obtiene los productos y enriquece con inventarios usando cache por producto."""
    try:
        productos_payload = consultar_productos_externo(params)
    except ProductoServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        logger.error("Error inesperado consultando microservicio de productos: %s", exc)
        raise InventarioServiceError({
            'error': 'Error inesperado consultando productos',
            'codigo': 'ERROR_INESPERADO'
        }, 500) from exc

    productos = _extract_productos(productos_payload)

    cache_client = CacheClient.from_app_config()
    resultado: List[Dict[str, Any]] = []
    sources: List[str] = []

    for producto in productos:
        if not isinstance(producto, MutableMapping):
            continue

        producto_id = producto.get('id') or producto.get('productoId')
        if producto_id is None:
            logger.warning("Producto sin ID, se omite: %s", producto)
            continue

        producto_id_str = str(producto_id)
        payload = _resolve_inventarios_from_cache(cache_client, producto_id_str)

        if payload is None:
            try:
                payload = _fetch_inventarios_from_upstream(producto_id_str)
            except InventarioServiceError as exc:
                # Propagamos para que el caller decida si retorna error o lista parcial
                raise exc
            _upsert_cache(cache_client, producto_id_str, payload)

        source = payload.get('source', 'cache')
        sources.append(source)

        resultado.append({
            **producto,
            'inventarios': payload.get('inventarios', []),
            'totalInventario': payload.get('totalInventario', 0),
            'inventariosSource': source
        })

    total = len(resultado)

    # Determinar la fuente predominante (si al menos uno viene del microservicio, marcamos microservices)
    source = 'cache'
    if any(s != 'cache' for s in sources):
        source = 'microservices'

    response: Dict[str, Any] = {
        'data': resultado,
        'total': total,
        'source': source
    }

    if isinstance(productos_payload, MutableMapping):
        response['meta'] = {
            key: productos_payload[key]
            for key in ('total', 'limit', 'offset', 'count')
            if key in productos_payload
        }

    return response

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


def actualizar_inventatrio_externo(producto_id: str, ajuste_cantidad: int) -> bool:
    """
    Actualiza el inventario de un producto en el microservicio de inventarios.

    Args:
        producto_id: ID del producto a actualizar.
        ajuste_cantidad: Cantidad a ajustar (positiva o negativa).

    Returns:
        Diccionario con la respuesta del microservicio.
    Raises:
        InventarioServiceError: Si ocurre un error de conexión o del microservicio.
    """
    inventarios_data = _get_inventarios_by_producto(producto_id)
    inventarios = inventarios_data.get('data', {}).get('inventarios', [])
    print(f"Todos los inventarios: {inventarios}")

    if not inventarios:
        raise InventarioServiceError({
            'error': 'No se encontraron inventarios para el producto',
            'codigo': 'INVENTARIOS_NO_ENCONTRADOS'
        }, 404)
    
    for inventario in inventarios:
        print(f"Inventario actual: {inventario}")
        cantidad = int(inventario.get('cantidad', 0))
        if cantidad + ajuste_cantidad < 0:
            raise InventarioServiceError({
                'error': 'No hay suficiente inventario para realizar el ajuste',
                'codigo': 'INVENTARIO_INSUFICIENTE'
            }, 400)
        _actualizar_inventario(str(inventario['id']), {'cantidad': cantidad + ajuste_cantidad})
        return True
    return False

def _actualizar_inventario(inventario_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza un inventario existente (delega al microservicio).
    
    Args:
        inventario_id: ID del inventario
        data: Datos a actualizar
    
    Returns:
        Inventario actualizado
    """
    try:
        inventarios_url = current_app.config.get('INVENTARIOS_URL')
        
        response = requests.put(
            f"{inventarios_url}/api/inventarios/{inventario_id}",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            inventario = response.json()
            logger.info(f"✅ Inventario actualizado: {inventario_id}")
            return inventario
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', f'Error {response.status_code}')
            logger.error(f"❌ Error actualizando inventario: {error_msg}")
            raise Exception(error_msg)
            
    except requests.RequestException as e:
        logger.error(f"❌ Error de conexión actualizando inventario: {e}")
        raise Exception(f"Error de conexión: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error actualizando inventario: {e}")
        raise Exception(f"Error actualizando inventario: {str(e)}")



def _get_inventarios_by_producto(producto_id: str) -> Dict[str, Any]:
    """
    Obtiene inventarios de un producto (cache-first strategy).
    
    1. Intenta leer del cache
    2. Si no está en cache, consulta el microservicio
    
    Args:
        producto_id: ID del producto
    
    Returns:
        Diccionario con inventarios y metadata
    """
    cache_client = CacheClient.from_app_config()
    
    # Intentar obtener del cache
    inventarios = cache_client.get_inventarios_by_producto(producto_id)
    source = 'cache'
    current_app.logger.info(f"inventarios (raw from cache): {inventarios}")

    # Si no está en cache, consultar microservicio
    if inventarios is None:
        current_app.logger.info(f"📡 Consultando microservicio para producto {producto_id}")
        inventarios = _get_from_microservice(producto_id)
        source = 'microservice'

    # Normalizar: el cache o la respuesta upstream puede devolver varias formas
    # (lista directa o un mapping con clave 'inventarios' u otras). Aseguramos
    # que `inventarios` sea una lista de mappings antes de operar sobre ella.
    if isinstance(inventarios, MutableMapping):
        # intentar extraer la lista de inventarios desde claves comunes
        for key in ('inventarios', 'data', 'items', 'results'):
            candidate = inventarios.get(key)
            if isinstance(candidate, list):
                inventarios = candidate
                break
        else:
            # no encontramos una lista; dejamos inventarios como vacío
            inventarios = []

    # A este punto, si no es lista, lo normalizamos a lista vacía
    if not isinstance(inventarios, list):
        current_app.logger.warning("Inventarios para producto %s devuelto en formato inesperado: %s", producto_id, type(inventarios))
        inventarios = []

    # Filtrar sólo items que sean mappings para evitar AttributeError
    inventarios = [inv for inv in inventarios if isinstance(inv, MutableMapping)]

    # Calcular totales de forma segura
    total_cantidad = sum(inv.get('cantidad', 0) for inv in inventarios)

    return {
        'data': {
            'productoId': producto_id,
            'inventarios': inventarios,
            'total': len(inventarios),
            'totalCantidad': total_cantidad,
            'source': source  # Útil para debugging
        }
    }
def _get_from_microservice(producto_id: str) -> List[Dict[str, Any]]:
    """
    Consulta inventarios directamente del microservicio (fallback).
    
    Args:
        producto_id: ID del producto
    
    Returns:
        Lista de inventarios
    """
    try:
        inventarios_url = current_app.config.get('INVENTARIOS_URL')

        logger.info(f"📡 Consultando microservicio para producto {producto_id}")
        print(f"{inventarios_url}/api/inventarios")
        
        response = requests.get(
            f"{inventarios_url}/api/inventarios",
            params={'productoId': producto_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            inventarios = data.get('inventarios', [])
            logger.info(f"✅ Inventarios obtenidos del microservicio: {len(inventarios)} items")
            return inventarios
        else:
            logger.error(f"❌ Error consultando microservicio: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error consultando microservicio de inventarios: {e}")
        return []