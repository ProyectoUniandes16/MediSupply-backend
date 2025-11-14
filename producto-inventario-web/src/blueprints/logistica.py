from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required
from src.services.logistica import (
    listar_zonas,
    obtener_zona_detallada,
    LogisticaServiceError
)

# Crear el blueprint para logística
logistica_bp = Blueprint('logistica', __name__)


@logistica_bp.route('/zona', methods=['GET'])
@jwt_required()
def consultar_zonas():
    """
    Endpoint para listar todas las zonas disponibles.
    
    Returns:
        JSON con la lista de zonas y total
    """
    try:
        resultado = listar_zonas()
        return jsonify(resultado), 200
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al consultar zonas: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al consultar zonas: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@logistica_bp.route('/zona/<zona_id>/detalle', methods=['GET'])
@jwt_required()
def consultar_zona_detallada(zona_id):
    """
    Endpoint para obtener el detalle completo de una zona con sus bodegas y camiones.
    
    Args:
        zona_id (str): ID de la zona a consultar
        
    Returns:
        JSON con el detalle de la zona, sus bodegas y camiones
    """
    try:
        resultado = obtener_zona_detallada(zona_id)
        return jsonify(resultado), 200
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al consultar zona detallada: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al consultar zona detallada: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
