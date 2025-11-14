from flask import Blueprint, request, jsonify, current_app
from src.services.visita_vendedor_service import (
    crear_visita_vendedor,
    actualizar_visita_vendedor,
    listar_visitas_vendedor,
    VisitaVendedorServiceError,
)

visitas_bp = Blueprint("visitas", __name__)


@visitas_bp.route("/visitas", methods=["POST"])
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


@visitas_bp.route("/visitas/<int:visita_id>", methods=["PATCH"])
def actualizar_visita_vendedor_endpoint(visita_id):
    """Endpoint para actualizar estado y observación de una visita."""
    try:
        data = request.get_json()
        visita = actualizar_visita_vendedor(visita_id, data)
        return jsonify(visita), 200
    except VisitaVendedorServiceError as err:
        return jsonify(err.message), err.status_code
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error("Error en actualizar visita vendedor: %s", str(exc))
        return (
            jsonify(
                {
                    "error": "Error interno del servidor",
                    "codigo": "ERROR_INTERNO_SERVIDOR",
                }
            ),
            500,
        )


@visitas_bp.route("/visitas", methods=["GET"])
@jwt_required()
def listar_visitas_vendedor_endpoint():
    """Endpoint para listar visitas filtradas por vendedor y rango opcional."""
    try:
        vendedor_id = request.args.get("vendedor_id")
        fecha_inicio = request.args.get("fecha_inicio")
        fecha_fin = request.args.get("fecha_fin")

        visitas = listar_visitas_vendedor(
            vendedor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return jsonify({"visitas": visitas}), 200
    except VisitaVendedorServiceError as err:
        return jsonify(err.message), err.status_code
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error("Error al listar visitas: %s", str(exc))
        return (
            jsonify(
                {
                    "error": "Error interno del servidor",
                    "codigo": "ERROR_INTERNO_SERVIDOR",
                }
            ),
            500,
        )
