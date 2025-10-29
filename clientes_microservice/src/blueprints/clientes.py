from flask import Blueprint, request, jsonify, current_app
from src.services.cliente_service import register_cliente, list_clientes, ClienteServiceError

# Crear el blueprint para clientes
clientes_bp = Blueprint('cliente', __name__)

@clientes_bp.route('/cliente', methods=['POST'])
def crear_cliente():
    """
    Endpoint para registrar un nuevo cliente
    """
    try:
        data = request.get_json()
        response_data = register_cliente(data)
        return jsonify(response_data), 201

    except ClienteServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en crear cliente: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500

@clientes_bp.route('/cliente', methods=['GET'])
def listar_clientes_endpoint():
    """
    Endpoint para listar clientes registrados.
    Actualmente retorna todos los clientes ordenados por nombre.
    """
    try:
        response_data = list_clientes(filtros=request.args or {})
        return jsonify(response_data), 200

    except ClienteServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en listar clientes: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500

