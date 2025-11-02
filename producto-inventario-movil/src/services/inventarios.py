"""Servicio para construir la vista de productos con inventarios para el BFF móvil.

Consulta directamente los microservicios de productos e inventarios y utiliza el
Redis Service como cache por producto.
"""
from __future__ import annotations

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
