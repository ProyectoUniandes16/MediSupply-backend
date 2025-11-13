from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from jwt import decode
from src.services.clientes import crear_cliente_externo, ClienteServiceError, listar_clientes_vendedor_externo
from src.utils.token_utils import decode_jwt
from src.services.vendedores import VendedorServiceError, asociar_cliente_a_vendedor
from src.services.auth import AuthServiceError, register_user

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
        datos_respuesta = crear_cliente_externo(datos_cliente)
        
        ## Asociar el cliente creado al vendedor
        cliente_id = datos_respuesta['data']['cliente']['id']
        if email_token and cliente_id:
            try:
                asociar_cliente_a_vendedor(email_token, cliente_id)
            except VendedorServiceError as e:
                # Loguear el error pero no impedir la creación del cliente en el BFF
                current_app.logger.error(f"Error al asociar cliente a vendedor: {e.message}")
            except Exception as e:
                # Capturar excepciones de requests u otras inesperadas y solo loguearlas
                current_app.logger.error(f"Error al asociar cliente a vendedor (no crítico): {str(e)}")
        
        ## Registrar el cliente como usuario en el sistema de autenticación
        registro_payload = {
            'email': datos_cliente.get('correo_empresa'),
            'password': 'defaultPassword123',  # Contraseña por defecto, se recomienda cambiarla luego
            'nombre': datos_cliente.get('nombre'),
        }
        
        try:
            register_user(registro_payload)
        except AuthServiceError as e:
            # No queremos que un fallo en el servicio de autenticación impida la creación del cliente
            current_app.logger.error(f"Error al registrar usuario: {e.message}")
        except Exception as e:
            current_app.logger.error(f"Error al registrar usuario: {str(e)}")

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

@clientes_bp.route('/cliente', methods=['GET'])
@jwt_required()
def listar_clientes():
    """
    Endpoint del BFF para listar clientes.
    Delega la lógica de negocio al servicio de clientes.
    """
    try:
        # Llamar a la capa de servicio para manejar la lógica
        vendedor_email = None
        token_data = decode_jwt(current_app, request.headers.get('Authorization'))
        vendedor_email = token_data.get('user').get('email') if token_data else None
        current_app.logger.info(f"Email from token: {vendedor_email}")
        datos_respuesta = listar_clientes_vendedor_externo(vendedor_email)

        return jsonify(datos_respuesta), 200
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