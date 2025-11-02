from flask import Blueprint, jsonify

# Crear el blueprint para health check
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - retorna 200 OK
    """
    return jsonify({"status": "healthy", "service": "auth-usuario"}), 200
