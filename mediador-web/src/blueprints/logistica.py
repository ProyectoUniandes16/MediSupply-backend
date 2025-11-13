from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required
from src.services.logistica import crear_visita_logistica, optimizar_ruta, LogisticaServiceError

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


@logistica_bp.route("/ruta-optima", methods=["POST"])
@jwt_required()
def optimizar_ruta_endpoint():
    """
    Endpoint BFF para optimizar rutas de entrega.
    
    Request Body:
        {
            "bodega": [-74.08175, 4.60971],
            "destinos": [
                [-74.0445, 4.6760],
                [-74.1475, 4.6165],
                [-74.1253, 4.7010]
            ]
        }
    
    Query Params:
        - formato: 'json' (default) o 'html'
        
    Returns:
        JSON con la ruta optimizada o HTML con el mapa interactivo
    """
    try:
        payload = request.get_json()
        formato = request.args.get("formato", "json").lower()
        
        resultado = optimizar_ruta(payload, formato=formato)
        
        # Si es HTML, retornar como Response con el content-type correcto
        if formato == "html":
            return Response(resultado, mimetype="text/html")
        
        # Si es JSON, retornar normalmente
        return jsonify(resultado), 200
        
    except LogisticaServiceError as err:
        return jsonify(err.message), err.status_code
    
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error(
            "Error inesperado optimizando ruta: %s",
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
