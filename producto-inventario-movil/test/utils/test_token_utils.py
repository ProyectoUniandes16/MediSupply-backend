import jwt
from src.utils.token_utils import decode_jwt
from src import create_app


def test_decode_jwt_no_token():
    app = create_app()
    with app.app_context():
        # No token -> function returns None
        assert decode_jwt(app, None) is None
        # Non-bearer token -> also None
        assert decode_jwt(app, 'Token sometoken') is None


def test_decode_jwt_valid_token():
    app = create_app()
    with app.app_context():
        # Configure secret and algorithm for decode
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['JWT_ALGORITHM'] = 'HS256'

        payload = {'user': {'email': 'user@example.com'}}
        token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])
        header = f'Bearer {token}'

        decoded = decode_jwt(app, header)
        assert decoded['user']['email'] == 'user@example.com'
