"""
Endpoints para operaciones de Cola (Pub/Sub)
"""
from flask import Blueprint, request, jsonify, current_app
from app.services.redis_service import redis_client

queue_bp = Blueprint('queue', __name__)


@queue_bp.route('/publish', methods=['POST'])
def publish_message():
    """
    Publicar mensaje en un canal
    
    POST /api/queue/publish
    Body: {
        "channel": "inventarios_updates",
        "message": {
            "event": "update",
            "producto_id": 123,
            "data": {...}
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'channel' not in data or 'message' not in data:
            return jsonify({
                'error': 'Se requieren los campos "channel" y "message"'
            }), 400
        
        channel = data['channel']
        message = data['message']
        
        subscribers = redis_client.queue_publish(channel, message)
        
        current_app.logger.info(f"📤 Mensaje publicado en '{channel}' - {subscribers} subscriptores")
        
        return jsonify({
            'message': 'Mensaje publicado',
            'channel': channel,
            'subscribers': subscribers
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@queue_bp.route('/channels', methods=['GET'])
def list_channels():
    """
    Listar canales activos
    
    GET /api/queue/channels?pattern=inventarios*
    """
    try:
        pattern = request.args.get('pattern', '*')
        channels = redis_client.queue_channels(pattern)
        
        # Obtener número de subscriptores por canal
        channels_info = []
        for channel in channels:
            num_subs = redis_client.queue_num_subscribers(channel)
            channels_info.append({
                'channel': channel,
                'subscribers': num_subs
            })
        
        return jsonify({
            'pattern': pattern,
            'count': len(channels_info),
            'channels': channels_info
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@queue_bp.route('/subscribers/<channel>', methods=['GET'])
def get_subscribers(channel):
    """
    Obtener número de subscriptores en un canal
    
    GET /api/queue/subscribers/{channel}
    """
    try:
        num_subs = redis_client.queue_num_subscribers(channel)
        
        return jsonify({
            'channel': channel,
            'subscribers': num_subs
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
