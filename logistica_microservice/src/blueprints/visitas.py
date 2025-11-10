from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from src.services.visita_vendedor_service import (
    crear_visita_vendedor,
    VisitaVendedorServiceError,
)

visitas_bp = Blueprint("visitas", __name__)


@visitas_bp.route("/visitas-vendedor", methods=["POST"])
@jwt_required()
def crear_visita_vendedor_endpoint():
    """Endpoint para crear una nueva visita de vendedor a un cliente."""
    try:
        data = request.get_json()
        visita = crear_visita_vendedor(data)
        return jsonify(visita), 201
    except VisitaVendedorServiceError as err:
        return jsonify(err.message), err.status_code
    except Exception as exc:  # pragma: no cover - log inesperado
        current_app.logger.error("Error en crear visita vendedor: %s", str(exc))
        return (
            jsonify(
                {
                    "error": "Error interno del servidor",
                    "codigo": "ERROR_INTERNO_SERVIDOR",
                }
            ),
            500,
        )
