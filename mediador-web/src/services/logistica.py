"""Servicio para interactuar con el microservicio de logistica."""
import logging
import os
from typing import Any, Dict, Optional

import requests
from flask import current_app


class LogisticaServiceError(Exception):
    """Errores controlados desde la capa de servicio de logistica."""

    def __init__(self, message: Dict[str, Any], status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _safe_log_error(message: str) -> None:
    """Loggea errores usando current_app si hay contexto, de lo contrario logging."""
    try:
        current_app.logger.error(message)
    except RuntimeError:
        logging.getLogger(__name__).error(message)


REQUIRED_FIELDS = ("cliente_id", "vendedor_id", "fecha_visita")


def _validar_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise LogisticaServiceError(
            {"error": "No se proporcionaron datos", "codigo": "DATOS_VACIOS"},
            400,
        )

    missing = [campo for campo in REQUIRED_FIELDS if not payload.get(campo)]
    if missing:
        raise LogisticaServiceError(
            {
                "error": f"Campos faltantes: {', '.join(missing)}",
                "codigo": "CAMPOS_FALTANTES",
            },
            400,
        )

    return payload


def crear_visita_logistica(
    payload: Optional[Dict[str, Any]],
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Invoca el microservicio de logistica para crear una visita."""
    datos = _validar_payload(payload)

    logistica_url = os.environ.get("LOGISTICA_URL", "http://localhost:5013")

    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    try:
        response = requests.post(
            f"{logistica_url}/visitas",
            json=datos,
            headers=request_headers,
            timeout=10,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            _safe_log_error(
                "Respuesta sin JSON del microservicio de logistica al crear visita",
            )
            raise LogisticaServiceError(
                {
                    "error": "Respuesta invalida del microservicio de logistica",
                    "codigo": "RESPUESTA_INVALIDA",
                },
                502,
            )
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else 500
        detalle = exc.response.text if exc.response else str(exc)
        _safe_log_error(
            f"Error HTTP del microservicio de logistica: {detalle}"
        )
        error_body: Dict[str, Any]
        if exc.response is not None:
            try:
                error_body = exc.response.json()
            except ValueError:
                error_body = {
                    "error": exc.response.text or "Error HTTP en logistica",
                    "codigo": "ERROR_HTTP",
                }
        else:
            error_body = {"error": "Error HTTP en logistica", "codigo": "ERROR_HTTP"}
        raise LogisticaServiceError(error_body, status_code)
    except requests.exceptions.RequestException as exc:
        _safe_log_error(f"Error de conexion con logistica: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error de conexion con el microservicio de logistica",
                "codigo": "ERROR_CONEXION",
            },
            503,
        )
    except LogisticaServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        _safe_log_error(f"Error inesperado creando visita en logistica: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error interno creando la visita",
                "codigo": "ERROR_INESPERADO",
            },
            500,
        )


def optimizar_ruta(
    payload: Optional[Dict[str, Any]],
    formato: str = "json",
) -> Any:
    """
    Invoca el microservicio de logística para optimizar una ruta de entrega.
    
    Args:
        payload: Diccionario con 'bodega' (coordenadas) y 'destinos' (lista de coordenadas)
        formato: 'json' o 'html' (por defecto 'json')
        
    Returns:
        Diccionario con la ruta optimizada o HTML del mapa según el formato
    """
    if not isinstance(payload, dict) or not payload:
        raise LogisticaServiceError(
            {"error": "No se proporcionaron datos", "codigo": "DATOS_VACIOS"},
            400,
        )
    
    if not payload.get("bodega"):
        raise LogisticaServiceError(
            {"error": "Campo 'bodega' es requerido", "codigo": "BODEGA_REQUERIDA"},
            400,
        )
    
    if not payload.get("destinos"):
        raise LogisticaServiceError(
            {"error": "Campo 'destinos' es requerido", "codigo": "DESTINOS_REQUERIDOS"},
            400,
        )
    
    logistica_url = os.environ.get("LOGISTICA_URL", "http://localhost:5013")
    
    try:
        response = requests.post(
            f"{logistica_url}/ruta-optima",
            json=payload,
            params={"formato": formato},
            headers={"Content-Type": "application/json"},
            timeout=30,  # Mayor timeout por el procesamiento de rutas
        )
        response.raise_for_status()
        
        # Si el formato es HTML, retornar el texto directamente
        if formato == "html":
            return response.text
        
        # Para JSON, parsear la respuesta
        try:
            return response.json()
        except ValueError:
            _safe_log_error(
                "Respuesta sin JSON del microservicio de logística al optimizar ruta",
            )
            raise LogisticaServiceError(
                {
                    "error": "Respuesta inválida del microservicio de logística",
                    "codigo": "RESPUESTA_INVALIDA",
                },
                502,
            )
    
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else 500
        detalle = exc.response.text if exc.response else str(exc)
        _safe_log_error(
            f"Error HTTP del microservicio de logística al optimizar ruta: {detalle}"
        )
        error_body: Dict[str, Any]
        if exc.response is not None:
            try:
                error_body = exc.response.json()
            except ValueError:
                error_body = {
                    "error": exc.response.text or "Error HTTP en logística",
                    "codigo": "ERROR_HTTP",
                }
        else:
            error_body = {"error": "Error HTTP en logística", "codigo": "ERROR_HTTP"}
        raise LogisticaServiceError(error_body, status_code)
    
    except requests.exceptions.Timeout:
        _safe_log_error("Timeout al optimizar ruta en logística")
        raise LogisticaServiceError(
            {
                "error": "Timeout al procesar la optimización de ruta",
                "codigo": "TIMEOUT",
            },
            504,
        )
    
    except requests.exceptions.RequestException as exc:
        _safe_log_error(f"Error de conexión con logística al optimizar ruta: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error de conexión con el microservicio de logística",
                "codigo": "ERROR_CONEXION",
            },
            503,
        )
    
    except LogisticaServiceError:
        raise
    
    except Exception as exc:  # pragma: no cover - defensivo
        _safe_log_error(f"Error inesperado al optimizar ruta: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error interno al optimizar ruta",
                "codigo": "ERROR_INESPERADO",
            },
            500,
        )
