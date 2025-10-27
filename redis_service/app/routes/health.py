"""
Health check endpoint
"""
from flask import Blueprint, jsonify
from app.services.redis_service import redis_client

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health():
    """Health check del servicio"""
    redis_status = redis_client.is_available()
    
    return jsonify({
        'service': 'redis_service',
        'status': 'healthy' if redis_status else 'degraded',
        'port': 5011,
        'redis': 'connected' if redis_status else 'disconnected'
    }), 200 if redis_status else 503


@health_bp.route('/stats', methods=['GET'])
def stats():
    """Estadísticas del servidor Redis"""
    try:
        stats_data = redis_client.get_stats()
        return jsonify(stats_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
