from flask import Blueprint, request, jsonify
from src.services.camion_service import (
    crear_camion,
    listar_camiones,
    obtener_camion,
    listar_camiones_por_bodega,
    actualizar_estado_camion,
    CamionServiceError
)

camiones_bp = Blueprint('camiones', __name__)


@camiones_bp.route('/camion', methods=['POST'])
def crear_camion_endpoint():
    """Endpoint para crear un camión"""
    try:
        data = request.get_json()
        resultado = crear_camion(data)
        return jsonify(resultado), 201
    except CamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@camiones_bp.route('/camion', methods=['GET'])
def listar_camiones_endpoint():
    """Endpoint para listar todos los camiones"""
    try:
        resultado = listar_camiones()
        return jsonify(resultado), 200
    except CamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@camiones_bp.route('/camion/<camion_id>', methods=['GET'])
def obtener_camion_endpoint(camion_id):
    """Endpoint para obtener un camión por ID"""
    try:
        resultado = obtener_camion(camion_id)
        return jsonify(resultado), 200
    except CamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@camiones_bp.route('/bodega/<bodega_id>/camiones', methods=['GET'])
def listar_camiones_bodega_endpoint(bodega_id):
    """Endpoint para listar camiones de una bodega específica"""
    try:
        resultado = listar_camiones_por_bodega(bodega_id)
        return jsonify(resultado), 200
    except CamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@camiones_bp.route('/camion/<camion_id>/estado', methods=['PATCH'])
def actualizar_estado_camion_endpoint(camion_id):
    """Endpoint para actualizar el estado de un camión"""
    try:
        data = request.get_json()
        if not data or 'estado' not in data:
            return jsonify({'error': 'El campo estado es requerido'}), 400
        
        resultado = actualizar_estado_camion(camion_id, data['estado'])
        return jsonify(resultado), 200
    except CamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
