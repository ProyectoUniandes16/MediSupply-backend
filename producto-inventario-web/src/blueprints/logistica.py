from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from src.services.logistica import (
    listar_zonas,
    obtener_zona_detallada,
    crear_ruta_entrega,
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


@logistica_bp.route('/rutas', methods=['POST'])
@jwt_required()
def crear_ruta():
    """
    Endpoint para crear una nueva ruta de entrega.
    
    Espera un JSON con los siguientes campos:
    - bodega_id (str): ID de la bodega de origen
    - camion_id (str): ID del camión asignado
    - zona_id (str): ID de la zona de entrega
    - estado (str): Estado inicial (pendiente, iniciado, en_progreso, completado, cancelado)
    - ruta (list): Lista de puntos de entrega, cada uno con:
        - ubicacion (list): [longitud, latitud]
        - pedido_id (str): ID del pedido a entregar
        
    Returns:
        JSON con la ruta creada y código 201
    """
    try:
        # Validar que se envió content-type application/json
        if not request.is_json:
            return jsonify({'error': 'Content-Type debe ser application/json'}), 400
            
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        resultado = crear_ruta_entrega(data)
        return jsonify(resultado), 201
        
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al crear ruta: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al crear ruta: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
