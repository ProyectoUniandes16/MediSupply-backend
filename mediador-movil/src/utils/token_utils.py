import re
import jwt as pyjwt

def decode_jwt(current_app, token)  -> dict:
    """
    Decodifica un token JWT sin verificar la firma.
    Útil para extraer información del token sin necesidad de la clave secreta.
    """
    raw_token = None
    if token and token.startswith('Bearer '):
        raw_token = token.split(' ', 1)[1]

    # Decodificar token (verificando firma) - requiere JWT_SECRET_KEY en config
    if raw_token:
        try:
            secret = current_app.config.get('JWT_SECRET_KEY')
            alg = current_app.config.get('JWT_ALGORITHM', 'HS256')
            # Decodificar y verificar firma
            decoded = pyjwt.decode(raw_token, secret, algorithms=[alg])
            return decoded
        except Exception as e:
            # Error al decodificar (firma inválida, token expirado, etc.)
            current_app.logger.error(f"Failed to decode JWT: {str(e)}")
            raise ValueError("Token inválido") from e