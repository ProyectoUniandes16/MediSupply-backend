from flask import Blueprint, request, jsonify, current_app, send_file
import json
import io
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.productos import ProductoServiceError
from src.services.productos import (
    crear_producto_externo, 
    procesar_y_enviar_producto_batch, 
    consultar_productos_externo,
    obtener_detalle_producto_externo,
    obtener_producto_por_sku_externo,
    descargar_certificacion_producto_externo
)

# Crear el blueprint para producto
producto_bp = Blueprint('producto', __name__)

@producto_bp.route('/producto', methods=['POST'])
@jwt_required()
def crear_producto():
    """
    Endpoint del BFF para crear un producto con inventario automático.
    Delega la lógica de negocio al servicio de productos.
    
    Campos requeridos en form-data:
    - nombre, codigo_sku, categoria, precio_unitario
    - condiciones_almacenamiento, fecha_vencimiento, proveedor_id
    - ubicacion (para inventario)
    - cantidad_inicial (para inventario)
    - certificacion (archivo)
    """
    try:   
        # Obtener datos del formulario
        data = request.form
        files = request.files        
        # Crear producto e inventario usando el servicio (orquestación)
        resultado = crear_producto_externo(data, files, get_jwt_identity())
        
        # Responder con producto e inventario creados
        print(f"BLUEPRINT - Producto e inventario creados: {resultado}")
        return jsonify({
            "data": resultado
        }), 201

    except ProductoServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        print(f"BLUEPRINT - Error en ProductoServiceError: {e.message}")
        return jsonify(e.message), e.status_code

    except Exception as e:
        print(f"BLUEPRINT - Error inesperado en producto: {str(e)}")
        # Capturar cualquier otro error no esperado
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500


@producto_bp.route('/producto-batch', methods=['POST'])
@jwt_required()
def producto_batch():
    """
    Endpoint para carga masiva de productos desde un CSV.
    - Valida el CSV y devuelve resumen con errores por fila.
    - Envía los productos válidos al microservicio de productos en chunks.
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No se proporcionó archivo', 'codigo': 'NO_FILE'}), 400

        user_id = get_jwt_identity()
        resultado = procesar_y_enviar_producto_batch(file, user_id)
        if resultado.get('ok'):
            return jsonify({'data': resultado.get('payload')}), resultado.get('status', 200)
        else:
            # payload es un string con el mensaje de error o un dict con detalles
            payload = resultado.get('payload')
            if isinstance(payload, dict):
                # si es dict, devolverlo directamente (ya contiene keys error/codigo)
                return jsonify(payload), resultado.get('status', 400)
            else:
                return jsonify({'error': str(payload), 'codigo': 'VALIDACION_ERROR'}), resultado.get('status', 400)

    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en producto-batch: {str(e)}")
        return jsonify({'error': 'Error interno', 'codigo': 'ERROR_INESPERADO'}), 500

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


@producto_bp.route('/producto/<int:producto_id>/certificacion', methods=['GET'])
@jwt_required()
def descargar_certificacion(producto_id):
    """
    Endpoint del BFF para descargar la certificación de un producto.
    Retorna el archivo PDF directamente desde el microservicio.
    """
    try:
        file_content, filename, mimetype = descargar_certificacion_producto_externo(producto_id)
        
        # Crear un objeto BytesIO para send_file
        file_stream = io.BytesIO(file_content)
        
        return send_file(
            file_stream,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado descargando certificación del producto {producto_id}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500