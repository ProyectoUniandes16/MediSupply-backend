from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from src.services.logistica import crear_visita_logistica, LogisticaServiceError

logistica_bp = Blueprint("logistica", __name__)


@logistica_bp.route("/visitas", methods=["POST"])
@jwt_required()
def crear_visita_logistica_endpoint():
    """Endpoint BFF para crear visitas en el microservicio de logistica."""
    try:
        payload = request.get_json()
        headers = {}
        auth_header = request.headers.get("Authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        visita = crear_visita_logistica(payload, headers=headers)
        return jsonify(visita), 201
    except LogisticaServiceError as err:
        return jsonify(err.message), err.status_code
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error(
            "Error inesperado creando visita logistica: %s",
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
