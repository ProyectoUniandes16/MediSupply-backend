from flask import Blueprint, request, jsonify, current_app

from src.services.pedidos import PedidoServiceError, registrar_pedido, listar_pedidos

# Crear el blueprint para clientes
pedidos_bp = Blueprint('pedido', __name__)

@pedidos_bp.route('/pedido', methods=['POST'])
def crear_pedido():
    """
    Endpoint para registrar un nuevo pedido
    """
    try:
        data = request.get_json()
        response_data = registrar_pedido(data)
        return jsonify(response_data), 201
    except PedidoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en crear pedido: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@pedidos_bp.route('/pedido', methods=['GET'])
def obtener_pedidos():
    """
    Endpoint para listar pedidos. Soporta query params opcionales:
    - vendedor_id
    - cliente_id
    """
    try:
        vendedor_id = request.args.get('vendedor_id')
        cliente_id = request.args.get('cliente_id')

        pedidos = listar_pedidos(vendedor_id=vendedor_id, cliente_id=cliente_id)
        return jsonify(pedidos), 200
    except PedidoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en obtener pedidos: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500