"""Servicios para interactuar con el microservicio de logistica desde el BFF movil."""
import logging
import os
from typing import Any, Dict, Optional

import requests
from flask import current_app


VALID_ESTADOS_VISITA = {"pendiente", "en progreso", "finalizado"}


class LogisticaServiceError(Exception):
    """Errores controlados para las operaciones con logistica."""

    def __init__(self, message: Dict[str, Any], status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _safe_log_error(message: str) -> None:
    """Registra errores en el logger disponible."""
    try:
        current_app.logger.error(message)
    except RuntimeError:
        logging.getLogger(__name__).error(message)


def _normalizar_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    datos = dict(payload)
    comentarios = datos.get("comentarios")
    if comentarios is not None:
        if not isinstance(comentarios, str):
            raise LogisticaServiceError(
                {
                    "error": "comentarios debe ser una cadena",
                    "codigo": "COMENTARIOS_INVALIDOS",
                },
                400,
            )
        comentarios = comentarios.strip()
        datos["comentarios"] = comentarios or None
    return datos


def _validar_entrada(visita_id: Optional[int], payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(visita_id, int) or visita_id <= 0:
        raise LogisticaServiceError(
            {
                "error": "visita_id debe ser un entero positivo",
                "codigo": "VISITA_ID_INVALIDO",
            },
            400,
        )

    if not isinstance(payload, dict) or not payload:
        raise LogisticaServiceError(
            {"error": "No se proporcionaron datos", "codigo": "DATOS_VACIOS"},
            400,
        )

    estado = payload.get("estado")
    if not isinstance(estado, str) or not estado:
        raise LogisticaServiceError(
            {
                "error": "Debe proporcionar el estado",
                "codigo": "ESTADO_REQUERIDO",
            },
            400,
        )
    if estado not in VALID_ESTADOS_VISITA:
        raise LogisticaServiceError(
            {
                "error": "Estado invalido. Valores permitidos: pendiente, en progreso, finalizado",
                "codigo": "ESTADO_INVALIDO",
            },
            400,
        )

    return _normalizar_payload(payload)


def actualizar_visita_logistica(
    visita_id: Optional[int],
    payload: Optional[Dict[str, Any]],
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Actualiza una visita en el microservicio de logistica."""
    datos = _validar_entrada(visita_id, payload)

    logistica_url = os.environ.get("LOGISTICA_URL", "http://localhost:5013")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    try:
        response = requests.patch(
            f"{logistica_url}/visitas/{visita_id}",
            json=datos,
            headers=request_headers,
            timeout=10,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            _safe_log_error(
                "Respuesta sin JSON del microservicio de logistica al actualizar visita",
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
        _safe_log_error(f"Error HTTP del microservicio de logistica: {detalle}")
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
        _safe_log_error(f"Error inesperado actualizando visita en logistica: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error interno actualizando la visita",
                "codigo": "ERROR_INESPERADO",
            },
            500,
        )
