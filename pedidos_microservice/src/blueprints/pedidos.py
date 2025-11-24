from flask import Blueprint, request, jsonify, current_app

from src.services.pedidos import PedidoServiceError, detalle_pedido, registrar_pedido, listar_pedidos

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
        estado = request.args.get('estado')
        pedidos = listar_pedidos(vendedor_id=vendedor_id, cliente_id=cliente_id, estado=estado)
        return jsonify(pedidos), 200
    except PedidoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en obtener pedidos: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500
    
@pedidos_bp.route('/pedido/<int:pedido_id>', methods=['GET'])
def obtener_detalle_pedido(pedido_id):
    """
    Endpoint para obtener el detalle de un pedido por su ID
    """
    try:
        pedido = detalle_pedido(pedido_id)
        return jsonify(pedido), 200
    except PedidoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en obtener detalle de pedido: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500


@pedidos_bp.route('/pedido/<int:pedido_id>/estado', methods=['PATCH'])
def actualizar_estado_pedido(pedido_id):
    """
    Endpoint para actualizar el estado de un pedido
    """
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        if not nuevo_estado:
            return jsonify({'error': 'Estado requerido', 'codigo': 'ESTADO_REQUERIDO'}), 400
        
        from src.services.pedidos import actualizar_estado_pedido as service_actualizar
        success = service_actualizar(pedido_id, nuevo_estado)
        if success:
            return jsonify({"message": "Estado actualizado"}), 200
        else:
            return jsonify({'error': 'Pedido no encontrado', 'codigo': 'PEDIDO_NO_ENCONTRADO'}), 404
    except PedidoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en actualizar estado de pedido: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
        }), 500