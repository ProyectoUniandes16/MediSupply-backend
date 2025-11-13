from flask import Blueprint, request, jsonify
from src.services.tipo_camion_service import (
    crear_tipo_camion,
    listar_tipos_camion,
    obtener_tipo_camion,
    inicializar_tipos_camion,
    TipoCamionServiceError
)

tipos_camion_bp = Blueprint('tipos_camion', __name__)


@tipos_camion_bp.route('/tipo-camion', methods=['POST'])
def crear_tipo_camion_endpoint():
    """Endpoint para crear un tipo de camión"""
    try:
        data = request.get_json()
        resultado = crear_tipo_camion(data)
        return jsonify(resultado), 201
    except TipoCamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tipos_camion_bp.route('/tipo-camion', methods=['GET'])
def listar_tipos_camion_endpoint():
    """Endpoint para listar todos los tipos de camión"""
    try:
        resultado = listar_tipos_camion()
        return jsonify(resultado), 200
    except TipoCamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tipos_camion_bp.route('/tipo-camion/<tipo_id>', methods=['GET'])
def obtener_tipo_camion_endpoint(tipo_id):
    """Endpoint para obtener un tipo de camión por ID"""
    try:
        resultado = obtener_tipo_camion(tipo_id)
        return jsonify(resultado), 200
    except TipoCamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tipos_camion_bp.route('/tipo-camion/inicializar', methods=['POST'])
def inicializar_tipos_camion_endpoint():
    """Endpoint para inicializar tipos de camión predeterminados"""
    try:
        resultado = inicializar_tipos_camion()
        return jsonify(resultado), 201
    except TipoCamionServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
