"""
Endpoints para operaciones de Cache
"""
from flask import Blueprint, request, jsonify
from app.services.redis_service import redis_client

cache_bp = Blueprint('cache', __name__)


@cache_bp.route('/<key>', methods=['GET'])
def get_cache(key):
    """
    Obtener valor del cache
    
    GET /api/cache/{key}
    """
    try:
        value = redis_client.cache_get(key)
        
        if value is None:
            return jsonify({
                'message': 'Clave no encontrada en cache',
                'key': key
            }), 404
        
        return jsonify({
            'key': key,
            'value': value,
            'ttl': redis_client.cache_ttl(key)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/', methods=['POST'])
def set_cache():
    """
    Guardar valor en cache
    
    POST /api/cache/
    Body: {
        "key": "mi_clave",
        "value": {...},
        "ttl": 3600  // opcional
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({
                'error': 'Se requieren los campos "key" y "value"'
            }), 400
        
        key = data['key']
        value = data['value']
        ttl = data.get('ttl')
        
        redis_client.cache_set(key, value, ttl)
        
        return jsonify({
            'message': 'Valor guardado en cache',
            'key': key,
            'ttl': ttl or redis_client.config['CACHE_DEFAULT_TTL']
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/<key>', methods=['DELETE'])
def delete_cache(key):
    """
    Eliminar clave del cache
    
    DELETE /api/cache/{key}
    """
    try:
        deleted = redis_client.cache_delete(key)
        
        if deleted == 0:
            return jsonify({
                'message': 'Clave no encontrada',
                'key': key
            }), 404
        
        return jsonify({
            'message': 'Clave eliminada del cache',
            'key': key
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/pattern/<pattern>', methods=['DELETE'])
def delete_cache_pattern(pattern):
    """
    Eliminar claves que coincidan con un patrón
    
    DELETE /api/cache/pattern/{pattern}
    Ejemplo: DELETE /api/cache/pattern/inventarios:*
    """
    try:
        deleted_count = redis_client.cache_delete_pattern(pattern)
        
        return jsonify({
            'message': f'Claves eliminadas',
            'pattern': pattern,
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/exists/<key>', methods=['GET'])
def exists_cache(key):
    """
    Verificar si una clave existe
    
    GET /api/cache/exists/{key}
    """
    try:
        exists = redis_client.cache_exists(key)
        
        return jsonify({
            'key': key,
            'exists': exists
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/keys', methods=['GET'])
def list_keys():
    """
    Listar claves que coincidan con un patrón
    
    GET /api/cache/keys?pattern=inventarios:*
    """
    try:
        pattern = request.args.get('pattern', '*')
        keys = redis_client.cache_keys(pattern)
        
        return jsonify({
            'pattern': pattern,
            'count': len(keys),
            'keys': keys
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/flush', methods=['POST'])
def flush_cache():
    """
    Limpiar todo el cache (¡usar con precaución!)
    
    POST /api/cache/flush
    Body: {
        "confirm": true
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('confirm'):
            return jsonify({
                'error': 'Se requiere confirmación explícita',
                'hint': 'Enviar {"confirm": true} en el body'
            }), 400
        
        redis_client.cache_flush()
        
        return jsonify({
            'message': 'Cache limpiado completamente'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
