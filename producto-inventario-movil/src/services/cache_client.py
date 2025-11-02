"""Cliente HTTP para interactuar con el Redis Service.

Este cliente encapsula las operaciones de cache necesarias para el BFF móvil
apoyado en el servicio redis_service (expuesto vía HTTP).
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import quote

import requests
from flask import current_app

logger = logging.getLogger(__name__)


class CacheClient:
    """Cliente ligero para Redis Service."""

    def __init__(self, base_url: str, default_ttl: int = 300, timeout: int = 3) -> None:
        self.base_url = base_url.rstrip('/')
        self.cache_endpoint = f"{self.base_url}/api/cache"
        self.default_ttl = default_ttl
        self.timeout = timeout

    @classmethod
    def from_app_config(cls) -> "CacheClient":
        cfg = current_app.config
        return cls(
            base_url=cfg.get('REDIS_SERVICE_URL', 'http://localhost:5011'),
            default_ttl=cfg.get('CACHE_DEFAULT_TTL', 300)
        )

    def _build_key(self, producto_id: str) -> str:
        return f"inventarios:producto:{producto_id}"

    def _encode_key(self, key: str) -> str:
        return quote(key, safe='')

    def get_inventarios_by_producto(self, producto_id: str) -> Optional[Any]:
        key = self._build_key(producto_id)
        try:
            response = requests.get(
                f"{self.cache_endpoint}/{self._encode_key(key)}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                payload = response.json()
                logger.info(
                    "Cache HIT en redis_service para producto %s", producto_id
                )
                return payload.get('value')
            if response.status_code == 404:
                logger.info(
                    "Cache MISS en redis_service para producto %s", producto_id
                )
                return None
            logger.warning(
                "Cache GET devolvió status inesperado %s para key %s",
                response.status_code,
                key
            )
            return None
        except requests.RequestException as exc:
            logger.warning("Error consultando cache: %s", exc)
            return None

    def set_inventarios_by_producto(self, producto_id: str, value: Any, ttl: Optional[int] = None) -> bool:
        key = self._build_key(producto_id)
        payload = {
            'key': key,
            'value': value,
            'ttl': ttl or self.default_ttl
        }
        try:
            response = requests.post(
                f"{self.cache_endpoint}/",
                json=payload,
                timeout=self.timeout
            )
            if response.status_code in (200, 201):
                logger.info(
                    "Cache SET en redis_service para producto %s (TTL %s)",
                    producto_id,
                    payload['ttl']
                )
                return True
            logger.warning(
                "No se pudo guardar cache para key %s. Status: %s",
                key,
                response.status_code
            )
            return False
        except requests.RequestException as exc:
            logger.warning("Error guardando en cache: %s", exc)
            return False

    def delete_producto_cache(self, producto_id: str) -> bool:
        key = self._build_key(producto_id)
        try:
            response = requests.delete(
                f"{self.cache_endpoint}/{self._encode_key(key)}",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as exc:
            logger.warning("Error eliminando cache para producto %s: %s", producto_id, exc)
            return False

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False
