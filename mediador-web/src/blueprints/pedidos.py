from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from src.services.pedidos import listar_pedidos, PedidosServiceError

# Crear el blueprint para pedidos
pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/pedido', methods=['GET'])
@jwt_required()
def listar_pedidos_endpoint():
    """
    Endpoint del BFF para listar pedidos.
    Soporta filtros opcionales por vendedor, cliente y zona.
    
    Query params:
        - vendedor_id (str, optional): Filtrar por ID de vendedor
        - cliente_id (str, optional): Filtrar por ID de cliente
        - zona (str, optional): Filtrar por zona del cliente
    """
    try:
        # Obtener parámetros de consulta
        vendedor_id = request.args.get('vendedor_id')
        cliente_id = request.args.get('cliente_id')
        zona = request.args.get('zona')
        
        # Obtener el token de autorización del request
        headers = {}
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        
        # Llamar a la capa de servicio
        datos_respuesta = listar_pedidos(
            vendedor_id=vendedor_id,
            cliente_id=cliente_id,
            zona=zona,
            headers=headers
        )
        
        return jsonify(datos_respuesta), 200

    except PedidosServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado al listar pedidos: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500

