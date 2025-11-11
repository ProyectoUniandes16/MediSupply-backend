from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required

from src.services.logistica import (
    actualizar_visita_logistica,
    listar_visitas_logistica,
    LogisticaServiceError,
)
from src.utils.token_utils import decode_jwt

logistica_bp = Blueprint("logistica_movil", __name__)


@logistica_bp.route("/visitas/<int:visita_id>", methods=["PATCH"])
@jwt_required()
def actualizar_visita_logistica_endpoint(visita_id):
    """Actualiza visitas de logistica para la aplicacion movil."""
    try:
        payload = request.get_json()
        headers = {}
        auth_header = request.headers.get("Authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        visita = actualizar_visita_logistica(visita_id, payload, headers=headers)
        return jsonify(visita), 200
    except LogisticaServiceError as err:
        return jsonify(err.message), err.status_code
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error(
            "Error inesperado actualizando visita logistica (movil): %s",
            str(exc),
        )


@logistica_bp.route("/visitas", methods=["GET"])
@jwt_required()
def listar_visitas_logistica_endpoint():
    """Lista visitas para el vendedor autenticado usando filtros opcionales."""
    try:
        filtros = request.args.to_dict(flat=True) or {}

        headers = {}
        auth_header = request.headers.get("Authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        token_data = decode_jwt(current_app, auth_header)
        vendedor_email = token_data.get("user", {}).get("email") if token_data else None

        visitas = listar_visitas_logistica(
            filtros=filtros,
            vendedor_email=vendedor_email,
            headers=headers,
        )
        return jsonify(visitas), 200
    except LogisticaServiceError as err:
        return jsonify(err.message), err.status_code
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error(
            "Error inesperado listando visitas de logística (móvil): %s",
            str(exc),
        )
        return (
            jsonify(
                {
                    "error": "Error interno del servidor",
                    "codigo": "ERROR_INTERNO_SERVIDOR",
                }
            ),
            500,
        )
        return (
            jsonify(
                {
                    "error": "Error interno del servidor",
                    "codigo": "ERROR_INTERNO_SERVIDOR",
                }
            ),
            500,
        )
