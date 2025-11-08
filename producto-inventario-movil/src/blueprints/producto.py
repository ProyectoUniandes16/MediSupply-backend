import re
from flask import Blueprint, request, jsonify, current_app, send_file
import json
import io
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.productos import ProductoServiceError
from src.services.productos import (
    obtener_detalle_producto_externo,
    obtener_producto_por_sku_externo,
    subir_video_producto_externo,
    aplanar_productos_con_inventarios,
    get_productos_con_inventarios
)
from src.services.inventarios import (
    InventarioServiceError,
    
)

# Crear el blueprint para producto
producto_bp = Blueprint('producto', __name__)

@producto_bp.route('/producto', methods=['GET'])
@jwt_required()
def consultar_productos():
    try:
        params = request.args.to_dict(flat=True) or None
        # El endpoint debe devolver lo que retorne `get_productos_con_inventarios`.
        # En tests se parchea esa función y se espera recibir la estructura agregada
        # (con campos 'data', 'total', 'source'). No aplanamos aquí.
        resultado = aplanar_productos_con_inventarios(get_productos_con_inventarios(params))
        return jsonify(resultado), 200
    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except InventarioServiceError as e:
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
        return jsonify({'data': detalle['producto']}), 200
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


@producto_bp.route('/producto/<int:producto_id>/videos', methods=['POST'])
@jwt_required()
def subir_video_producto(producto_id):
    """
    Endpoint del BFF para subir un video de evidencia para un producto.
    
    Validaciones:
    - Formato: MP4, MOV, AVI
    - Tamaño máximo: 150 MB
    - Descripción obligatoria
    
    Form-data esperado:
        - video: Archivo de video
        - descripcion: Descripción del video (obligatorio)
        
    Returns:
        201: Video subido exitosamente
        400: Datos inválidos
        404: Producto no encontrado
        413: Archivo muy grande
        500: Error interno
    """
    try:
        # Validar que se envió un archivo
        if 'video' not in request.files:
            return jsonify({
                'error': 'No se proporcionó ningún archivo de video',
                'codigo': 'ARCHIVO_FALTANTE',
                'campo_esperado': 'video'
            }), 400
        
        video_file = request.files['video']
        
        # Validar nombre de archivo
        if not video_file.filename or video_file.filename == '':
            return jsonify({
                'error': 'El archivo no tiene nombre',
                'codigo': 'ARCHIVO_INVALIDO'
            }), 400
        
        # Validar descripción
        descripcion = request.form.get('descripcion', '').strip()
        if not descripcion:
            return jsonify({
                'error': 'La descripción del video es obligatoria',
                'codigo': 'DESCRIPCION_FALTANTE'
            }), 400
        
        # Obtener usuario del JWT
        usuario_registro = get_jwt_identity()
        
        # Delegar al microservicio de productos
        resultado = subir_video_producto_externo(
            producto_id=producto_id,
            video_file=video_file,
            descripcion=descripcion,
            usuario_registro=usuario_registro
        )
        
        return jsonify(resultado), 201
        
    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado subiendo video para producto {producto_id}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500
