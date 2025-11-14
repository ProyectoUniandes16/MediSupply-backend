from flask import Blueprint, request, jsonify, current_app
from src.services.zona_service import (
    crear_zona, 
    listar_zonas, 
    obtener_zona,
    listar_zonas_con_bodegas,
    obtener_zona_detallada,
    inicializar_zonas,
    ZonaServiceError
)

# Crear el blueprint para zonas
zonas_bp = Blueprint('zonas', __name__)


@zonas_bp.route('/zona', methods=['POST'])
def crear_zona_endpoint():
    """
    Endpoint para crear una nueva zona
    """
    try:
        data = request.get_json()
        response_data = crear_zona(data)
        return jsonify(response_data), 201
    except ZonaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en crear zona: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@zonas_bp.route('/zona', methods=['GET'])
def listar_zonas_endpoint():
    """
    Endpoint para listar todas las zonas
    """
    try:
        zonas = listar_zonas()
        return jsonify(zonas), 200
    except ZonaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en listar zonas: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@zonas_bp.route('/zona/<zona_id>', methods=['GET'])
def obtener_zona_endpoint(zona_id):
    """
    Endpoint para obtener una zona por ID
    """
    try:
        zona = obtener_zona(zona_id)
        return jsonify(zona), 200
    except ZonaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en obtener zona: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@zonas_bp.route('/zona-con-bodegas', methods=['GET'])
def listar_zonas_con_bodegas_endpoint():
    """
    Endpoint para listar zonas con sus bodegas asociadas
    """
    try:
        zonas = listar_zonas_con_bodegas()
        return jsonify(zonas), 200
    except ZonaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en listar zonas con bodegas: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@zonas_bp.route('/zona/<zona_id>/detalle', methods=['GET'])
def obtener_zona_detallada_endpoint(zona_id):
    """
    Endpoint para obtener el detalle completo de una zona con bodegas y camiones
    """
    try:
        zona = obtener_zona_detallada(zona_id)
        return jsonify(zona), 200
    except ZonaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en obtener zona detallada: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@zonas_bp.route('/zona/inicializar', methods=['POST'])
def inicializar_zonas_endpoint():
    """
    Endpoint para inicializar las zonas por defecto con sus bodegas y camiones.
    
    Crea 4 zonas (México DF, Bogotá, Quito, Lima) cada una con:
    - Una bodega central
    - 3 camiones (uno de cada tipo: Refrigerado, Sin Refrigeración, Mixto)
    
    Nota: Requiere que los tipos de camión estén previamente inicializados.
    """
    try:
        resultado = inicializar_zonas()
        return jsonify(resultado), 201
    except ZonaServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en inicializar zonas: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500
