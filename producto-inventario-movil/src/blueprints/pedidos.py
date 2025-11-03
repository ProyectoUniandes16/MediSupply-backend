from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.token_utils import decode_jwt
from src.services.pedidos import crear_pedido_externo, PedidoServiceError


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