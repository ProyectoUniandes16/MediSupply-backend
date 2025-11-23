from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from src.services.logistica import (
    listar_zonas,
    listar_bodegas,
    listar_zonas_con_bodegas,
    obtener_zona_detallada,
    crear_ruta_entrega,
    optimizar_ruta,
    listar_rutas_logistica,
    obtener_ruta_detallada,
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


@logistica_bp.route('/bodega', methods=['GET'])
@jwt_required()
def consultar_bodegas():
    """
    Endpoint para listar todas las bodegas disponibles.
    
    Returns:
        JSON con la lista de bodegas y total
    """
    try:
        resultado = listar_bodegas()
        return jsonify(resultado), 200
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al consultar bodegas: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al consultar bodegas: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@logistica_bp.route('/zona-con-bodegas', methods=['GET'])
@jwt_required()
def consultar_zonas_con_bodegas():
    """
    Endpoint para listar todas las zonas con sus bodegas asociadas.
    
    Returns:
        JSON con la lista de zonas con bodegas y total
    """
    try:
        resultado = listar_zonas_con_bodegas()
        return jsonify(resultado), 200
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al consultar zonas con bodegas: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al consultar zonas con bodegas: {str(e)}")
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


@logistica_bp.route('/ruta-optima', methods=['POST'])
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
        # Validar que se envió content-type application/json
        if not request.is_json:
            return jsonify({'error': 'Content-Type debe ser application/json'}), 400
            
        payload = request.get_json()
        
        if not payload:
            return jsonify({'error': 'No se proporcionaron datos', 'codigo': 'DATOS_VACIOS'}), 400
        
        formato = request.args.get('formato', 'json').lower()
        
        resultado = optimizar_ruta(payload, formato=formato)
        
        # Si es HTML, retornar como Response con el content-type correcto
        if formato == 'html':
            from flask import Response
            return Response(resultado, mimetype='text/html')
        
        # Si es JSON, retornar normalmente
        return jsonify(resultado), 200
        
    except LogisticaServiceError as e:
        return jsonify(e.message), e.status_code
    
    except Exception as exc:
        current_app.logger.error(
            f"Error inesperado optimizando ruta: {str(exc)}"
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


@logistica_bp.route('/rutas', methods=['GET'])
@jwt_required()
def listar_rutas():
    """
    Endpoint para listar rutas con filtros opcionales.
    
    Query Params:
        - estado: Estado de la ruta (pendiente, iniciado, en_progreso, completado, cancelado)
        - zona_id: ID de la zona
        - camion_id: ID del camión
        - bodega_id: ID de la bodega
        
    Returns:
        JSON con la lista de rutas y total
    """
    try:
        # Obtener filtros de los query params
        filtros = {}
        
        if request.args.get('estado'):
            filtros['estado'] = request.args.get('estado')
        
        if request.args.get('zona_id'):
            filtros['zona_id'] = request.args.get('zona_id')
        
        if request.args.get('camion_id'):
            filtros['camion_id'] = request.args.get('camion_id')
        
        if request.args.get('bodega_id'):
            filtros['bodega_id'] = request.args.get('bodega_id')
        
        resultado = listar_rutas_logistica(filtros if filtros else None)
        return jsonify(resultado), 200
        
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al listar rutas: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al listar rutas: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@logistica_bp.route('/rutas/<ruta_id>', methods=['GET'])
@jwt_required()
def obtener_ruta(ruta_id):
    """
    Endpoint para obtener una ruta específica por su ID.
    
    Args:
        ruta_id (str): ID de la ruta a consultar
        
    Returns:
        JSON con los datos de la ruta y sus detalles
    """
    try:
        resultado = obtener_ruta_detallada(ruta_id)
        return jsonify(resultado), 200
        
    except LogisticaServiceError as e:
        current_app.logger.error(f"Error al obtener ruta: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado al obtener ruta: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
