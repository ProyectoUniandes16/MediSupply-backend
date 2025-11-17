from re import I
from unittest import result
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.token_utils import decode_jwt
from src.services.pedidos import crear_pedido_externo, PedidoServiceError, listar_pedidos_externo, detalle_pedido_externo
from src.services.productos import obtener_detalle_producto_externo

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/pedido', methods=['POST'])
@jwt_required()
def crear_pedido():
    """
    Endpoint del BFF para crear un pedido.
    Delega la lógica de negocio al servicio de pedidos.
    """
    try:
        datos_pedido = request.get_json()
        token_data = decode_jwt(current_app, request.headers.get('Authorization'))
        email_token = token_data.get('user').get('email') if token_data else None
        current_app.logger.info(f"Email from token: {email_token}")
        # Llamar a la capa de servicio para manejar la lógica
        datos_respuesta = crear_pedido_externo(datos_pedido, vendedor_email=email_token)
        current_app.logger.info(f"Respuesta del servicio de pedidos: {datos_respuesta}")
        return jsonify(datos_respuesta), 201

    except PedidoServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        # usar logger.exception para incluir traceback completo en los logs
        current_app.logger.exception(f"Error inesperado en el blueprint de pedido: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@pedidos_bp.route('/pedido', methods=['GET'])
@jwt_required()
def listar_pedidos():
    """Endpoint del BFF para listar pedidos delegando en la capa de servicios."""
    try:
        filtros = request.args.to_dict(flat=True) or {}
        token_data = decode_jwt(current_app, request.headers.get('Authorization'))
        email_token = None
        if token_data:
            email_token = token_data.get('user', {}).get('email')
        rol = token_data.get('user', {}).get('rol') if token_data else None

        datos_respuesta = listar_pedidos_externo(filtros=filtros, email=email_token, rol=rol)
        return jsonify(datos_respuesta), 200
    except PedidoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:  # pragma: no cover - defensivo
        current_app.logger.exception(f"Error inesperado listando pedidos: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500
    
@pedidos_bp.route('/pedido/<int:pedido_id>', methods=['GET'])
def detalle_pedido(pedido_id):
    """Endpoint para obtener el detalle de un pedido específico."""
    try:
        detalle_pedido = detalle_pedido_externo(pedido_id)
        resultado = detalle_pedido
        productos = []
        for producto in detalle_pedido['data']['productos']:
            producto_id = producto.get('producto_id')
            detalle_producto = obtener_detalle_producto_externo(producto_id)
            producto_data = detalle_producto.get('producto', {})
            item = {
                'cantidad': producto.get('cantidad'),
                'producto': producto_data
            }
            productos.append(item)
        resultado['data']['productos'] = productos
        return jsonify(resultado), 200
    except Exception as e:
        current_app.logger.exception(f"Error obteniendo detalle del pedido {pedido_id}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500