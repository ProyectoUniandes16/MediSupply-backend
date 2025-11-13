from flask import Blueprint, request, jsonify, current_app
from src.services.bodega_service import (
    crear_bodega, 
    listar_bodegas, 
    obtener_bodega,
    BodegaServiceError
)

# Crear el blueprint para bodegas
bodegas_bp = Blueprint('bodegas', __name__)


@bodegas_bp.route('/bodega', methods=['POST'])
def crear_bodega_endpoint():
    """
    Endpoint para crear una nueva bodega en una zona
    """
    try:
        data = request.get_json()
        response_data = crear_bodega(data)
        return jsonify(response_data), 201
    except BodegaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en crear bodega: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@bodegas_bp.route('/bodega', methods=['GET'])
def listar_bodegas_endpoint():
    """
    Endpoint para listar todas las bodegas
    """
    try:
        bodegas = listar_bodegas()
        return jsonify(bodegas), 200
    except BodegaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en listar bodegas: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@bodegas_bp.route('/bodega/<bodega_id>', methods=['GET'])
def obtener_bodega_endpoint(bodega_id):
    """
    Endpoint para obtener una bodega por ID
    """
    try:
        bodega = obtener_bodega(bodega_id)
        return jsonify(bodega), 200
    except BodegaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en obtener bodega: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500
