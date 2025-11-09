from flask import Blueprint

# Blueprint para health check
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado del servicio
    """
    return {'status': 'healthy', 'service': 'logistica-microservice'}, 200
