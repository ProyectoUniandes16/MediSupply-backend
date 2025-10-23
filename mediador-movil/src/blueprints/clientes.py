from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from jwt import decode
from src.services.clientes import crear_cliente_externo, ClienteServiceError
from src.utils.token_utils import decode_jwt

# Crear el blueprint para clientes
clientes_bp = Blueprint('cliente', __name__)

@clientes_bp.route('/cliente', methods=['POST'])
@jwt_required()
def crear_cliente():
    """
    Endpoint del BFF para crear un cliente.
    Delega la lógica de negocio al servicio de clientes.
    """
    try:
        datos_cliente = request.get_json()
        token_data = decode_jwt(current_app, request.headers.get('Authorization'))
        email_token = token_data.get('user').get('email') if token_data else None
        current_app.logger.info(f"Email from token: {email_token}")
        # Llamar a la capa de servicio para manejar la lógica
        datos_respuesta = crear_cliente_externo(datos_cliente, vendedor_email=email_token)

        return jsonify(datos_respuesta), 201

    except ClienteServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en el blueprint de cliente: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500
