from flask import Blueprint, request, jsonify, current_app, send_file
import json
import io
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.productos import ProductoServiceError
from src.services.productos import (
    consultar_productos_externo,
    obtener_detalle_producto_externo,
    obtener_producto_por_sku_externo
)

# Crear el blueprint para prod  ucto
producto_bp = Blueprint('producto', __name__)

@producto_bp.route('/producto', methods=['GET'])
@jwt_required()
def consultar_productos():
    try:
        # Lógica para consultar productos (a implementar)
        productos = consultar_productos_externo(request.args)
        return jsonify({'data': productos}), 200
    except ProductoServiceError as e:
        # Retornar contenido y código del error personalizado
        return jsonify(e.message), e.status_code
    except Exception:
        # Retornar error genérico como JSON con status 500
        return jsonify({'error': 'Error interno del servidor', 'codigo': 'ERROR_INESPERADO'}), 500


@producto_bp.route('/producto/<int:producto_id>', methods=['GET'])
@jwt_required()
def obtener_detalle_producto(producto_id):
    """
    Endpoint del BFF para obtener el detalle completo de un producto.
    Delega al microservicio de productos.
    """
    try:
        detalle = obtener_detalle_producto_externo(producto_id)
        return jsonify({'data': detalle}), 200
    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle de producto {producto_id}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500


@producto_bp.route('/producto/sku/<string:sku>', methods=['GET'])
@jwt_required()
def obtener_producto_por_sku(sku):
    """
    Endpoint del BFF para buscar un producto por su código SKU.
    Delega al microservicio de productos.
    """
    try:
        producto = obtener_producto_por_sku_externo(sku)
        return jsonify({'data': producto}), 200
    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado buscando producto por SKU {sku}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500
