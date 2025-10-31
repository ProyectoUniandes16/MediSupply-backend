"""
Blueprint para consultar inventarios de productos.
"""
from flask import Blueprint, jsonify, request
from src.services.inventarios_service import InventariosService
import logging

logger = logging.getLogger(__name__)

inventarios_bp = Blueprint('inventarios', __name__)


# ============================================
# ENDPOINTS DE LECTURA
# ============================================

@inventarios_bp.route('/productos/<producto_id>/inventarios', methods=['GET'])
def get_inventarios_producto(producto_id):
    """
    Obtiene los inventarios de un producto (desde cache).
    
    GET /api/productos/{producto_id}/inventarios
    """
    try:
        result = InventariosService.get_inventarios_by_producto(producto_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error consultando inventarios: {e}")
        return jsonify({
            'error': 'Error consultando inventarios',
            'detalle': str(e)
        }), 500


@inventarios_bp.route('/productos/<producto_id>/disponible', methods=['GET'])
def get_disponible_producto(producto_id):
    """
    Obtiene el total disponible de un producto.
    
    GET /api/productos/{producto_id}/disponible
    """
    try:
        total = InventariosService.get_total_disponible(producto_id)
        
        return jsonify({
            'productoId': producto_id,
            'totalDisponible': total
        }), 200
        
    except Exception as e:
        logger.error(f"Error consultando disponibilidad: {e}")
        return jsonify({
            'error': 'Error consultando disponibilidad',
            'detalle': str(e)
        }), 500


@inventarios_bp.route('/productos', methods=['GET'])
def get_productos_con_inventarios():
    """Obtiene todos los productos con sus inventarios embebidos (cache-first)."""
    try:
        filtros = {
            'categoria': request.args.get('categoria'),
            'estado': request.args.get('estado')
        }
        filtros = {clave: valor for clave, valor in filtros.items() if valor}

        result = InventariosService.get_productos_con_inventarios(filtros)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error consultando productos con inventarios: {e}")
        return jsonify({
            'error': 'Error consultando productos con inventarios',
            'detalle': str(e)
        }), 500


# ============================================
# ENDPOINTS DE ESCRITURA (Mediador)
# ============================================

@inventarios_bp.route('/inventarios', methods=['POST'])
def crear_inventario():
    """
    Crea un nuevo inventario (delega al microservicio).
    
    POST /api/inventarios
    Body: {
        "productoId": "123",
        "cantidad": 50,
        "ubicacion": "A1",
        "usuario": "admin"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Se requiere body con datos del inventario'}), 400
        
        inventario = InventariosService.crear_inventario(data)
        
        return jsonify(inventario), 201
        
    except Exception as e:
        logger.error(f"Error creando inventario: {e}")
        return jsonify({
            'error': 'Error creando inventario',
            'detalle': str(e)
        }), 400 if 'ya existe' in str(e).lower() or 'requerido' in str(e).lower() else 500


@inventarios_bp.route('/inventarios/<inventario_id>', methods=['PUT'])
def actualizar_inventario(inventario_id):
    """
    Actualiza un inventario existente (delega al microservicio).
    
    PUT /api/inventarios/{inventario_id}
    Body: {
        "cantidad": 75,
        "ubicacion": "B2",
        "usuario": "admin"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Se requiere body con datos a actualizar'}), 400
        
        inventario = InventariosService.actualizar_inventario(inventario_id, data)
        
        return jsonify(inventario), 200
        
    except Exception as e:
        logger.error(f"Error actualizando inventario: {e}")
        return jsonify({
            'error': 'Error actualizando inventario',
            'detalle': str(e)
        }), 404 if 'no encontrado' in str(e).lower() else 400 if 'ya existe' in str(e).lower() else 500


@inventarios_bp.route('/inventarios/<inventario_id>', methods=['DELETE'])
def eliminar_inventario(inventario_id):
    """
    Elimina un inventario (delega al microservicio).
    
    DELETE /api/inventarios/{inventario_id}
    Body (opcional): {
        "usuario": "admin"
    }
    """
    try:
        data = request.get_json() or {}
        usuario = data.get('usuario')
        
        InventariosService.eliminar_inventario(inventario_id, usuario)
        
        return jsonify({
            'mensaje': 'Inventario eliminado exitosamente',
            'inventarioId': inventario_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminando inventario: {e}")
        return jsonify({
            'error': 'Error eliminando inventario',
            'detalle': str(e)
        }), 404 if 'no encontrado' in str(e).lower() else 500


@inventarios_bp.route('/inventarios/<inventario_id>/ajustar', methods=['POST'])
def ajustar_cantidad(inventario_id):
    """
    Ajusta la cantidad de un inventario (+/-).
    
    POST /api/inventarios/{inventario_id}/ajustar
    Body: {
        "ajuste": -10,
        "usuario": "admin"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'ajuste' not in data:
            return jsonify({'error': 'Se requiere el campo "ajuste"'}), 400
        
        ajuste = data.get('ajuste')
        usuario = data.get('usuario')
        
        if not isinstance(ajuste, int):
            return jsonify({'error': 'El ajuste debe ser un número entero'}), 400
        
        inventario = InventariosService.ajustar_cantidad(inventario_id, ajuste, usuario)
        
        return jsonify(inventario), 200
        
    except Exception as e:
        logger.error(f"Error ajustando cantidad: {e}")
        return jsonify({
            'error': 'Error ajustando cantidad',
            'detalle': str(e)
        }), 404 if 'no encontrado' in str(e).lower() else 400 if 'negativa' in str(e).lower() else 500


# ============================================
# ENDPOINTS DE HEALTH/DEBUG
# ============================================

@inventarios_bp.route('/health/cache', methods=['GET'])
def cache_health():
    """Verifica el estado del cache."""
    try:
        from src.services.cache_client import CacheClient
        from flask import current_app
        
        redis_url = current_app.config.get('REDIS_SERVICE_URL')
        cache_client = CacheClient(redis_url)
        
        is_available = cache_client.is_available()
        
        return jsonify({
            'cache': 'available' if is_available else 'unavailable',
            'redis_service_url': redis_url
        }), 200 if is_available else 503
        
    except Exception as e:
        return jsonify({
            'cache': 'error',
            'error': str(e)
        }), 500
