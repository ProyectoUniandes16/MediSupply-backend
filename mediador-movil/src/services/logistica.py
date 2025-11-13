"""Servicios para interactuar con el microservicio de logistica desde el BFF movil."""
import logging
import os
from typing import Any, Dict, Optional, Iterable

import requests
from flask import current_app

from src.services.vendedores import listar_vendedores_externo, VendedorServiceError
from src.config.config import Config


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


def listar_visitas_logistica(
    filtros: Optional[Dict[str, Any]] = None,
    vendedor_email: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Consulta visitas en logística aplicando filtros y resolviendo el vendedor desde el token."""
    filtros_seguro: Dict[str, Any] = dict(filtros or {})

    if vendedor_email:
        try:
            vendedores_response = listar_vendedores_externo(filters={"correo": vendedor_email})
        except VendedorServiceError as exc:
            raise LogisticaServiceError(
                {
                    "error": "Error al consultar vendedor",
                    "codigo": "ERROR_VENDEDOR",
                },
                exc.status_code,
            ) from exc

        items = vendedores_response.get("items") if isinstance(vendedores_response, dict) else None
        if not items:
            raise LogisticaServiceError(
                {
                    "error": "Vendedor no encontrado",
                    "codigo": "VENDEDOR_NO_ENCONTRADO",
                },
                404,
            )

        vendedor_id = items[0].get("id")
        if not vendedor_id:
            raise LogisticaServiceError(
                {
                    "error": "Vendedor sin identificador válido",
                    "codigo": "VENDEDOR_SIN_ID",
                },
                404,
            )
        filtros_seguro["vendedor_id"] = vendedor_id

    logistica_url = os.environ.get("LOGISTICA_URL", "http://localhost:5013")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    try:
        response = requests.get(
            f"{logistica_url}/visitas",
            params=filtros_seguro or None,
            headers=request_headers,
            timeout=10,
        )

        if response.status_code != 200:
            _safe_log_error(
                f"Error del microservicio de logistica al listar: {response.status_code} - {response.text}"
            )
            try:
                error_body = response.json()
            except ValueError:
                error_body = {
                    "error": "Error al listar visitas en logística",
                    "codigo": "ERROR_LOGISTICA",
                }
            raise LogisticaServiceError(error_body, response.status_code)

        try:
            data = response.json()
        except ValueError as exc:
            _safe_log_error("Respuesta sin JSON del microservicio de logistica al listar visitas")
            raise LogisticaServiceError(
                {
                    "error": "Respuesta inválida del microservicio de logistica",
                    "codigo": "RESPUESTA_INVALIDA",
                },
                502,
            ) from exc

        visitas = data.get("visitas") if isinstance(data, dict) else None
        if isinstance(visitas, list) and visitas:
            cliente_ids = {
                visita.get("cliente_id")
                for visita in visitas
                if visita.get("cliente_id") is not None
            }
            if cliente_ids:
                clientes_map = _obtener_clientes_por_ids(cliente_ids, headers=headers)
                for visita in visitas:
                    cliente_id = visita.get("cliente_id")
                    visita["cliente"] = clientes_map.get(str(cliente_id)) if cliente_id is not None else None

        return data

    except requests.exceptions.RequestException as exc:
        _safe_log_error(f"Error de conexion con logistica al listar visitas: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error de conexion con el microservicio de logistica",
                "codigo": "ERROR_CONEXION",
            },
            503,
        ) from exc
    except LogisticaServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        _safe_log_error(f"Error inesperado listando visitas en logistica: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error interno al listar visitas",
                "codigo": "ERROR_INESPERADO",
            },
            500,
        ) from exc


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


def _obtener_clientes_por_ids(
    cliente_ids: Iterable[Any],
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    ids_list = [cid for cid in cliente_ids if cid is not None]
    if not ids_list:
        return {}

    clientes_url = Config.CLIENTES_URL
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    try:
        response = requests.get(
            f"{clientes_url}/cliente",
            params={"ids": ",".join(str(cid) for cid in ids_list)},
            headers=request_headers,
            timeout=10,
        )
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            _safe_log_error("Respuesta sin JSON del microservicio de clientes al obtener detalles")
            raise LogisticaServiceError(
                {
                    "error": "Respuesta inválida del microservicio de clientes",
                    "codigo": "RESPUESTA_CLIENTES_INVALIDA",
                },
                502,
            ) from exc

        clientes = data.get("data") if isinstance(data, dict) else None
        if not isinstance(clientes, list):
            clientes = []

        mapa: Dict[str, Dict[str, Any]] = {}
        for cliente in clientes:
            cliente_id = cliente.get("id")
            if cliente_id is None:
                continue
            mapa[str(cliente_id)] = cliente
        return mapa

    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else 500
        detalle = exc.response.text if exc.response else str(exc)
        _safe_log_error(f"Error HTTP del microservicio de clientes: {detalle}")
        if exc.response is not None:
            try:
                error_body = exc.response.json()
            except ValueError:
                error_body = {
                    "error": "Error del microservicio de clientes",
                    "codigo": "ERROR_CLIENTES_HTTP",
                }
        else:
            error_body = {
                "error": "Error del microservicio de clientes",
                "codigo": "ERROR_CLIENTES_HTTP",
            }
        raise LogisticaServiceError(error_body, status_code) from exc
    except requests.exceptions.RequestException as exc:
        _safe_log_error(f"Error de conexion con el microservicio de clientes: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error de conexion con el microservicio de clientes",
                "codigo": "ERROR_CLIENTES_CONEXION",
            },
            503,
        ) from exc
    except LogisticaServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        _safe_log_error(f"Error inesperado obteniendo clientes: {str(exc)}")
        raise LogisticaServiceError(
            {
                "error": "Error interno obteniendo clientes",
                "codigo": "ERROR_CLIENTES_INESPERADO",
            },
            500,
        ) from exc
