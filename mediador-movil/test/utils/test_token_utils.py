import pytest
from flask import Flask
import jwt as pyjwt

from src.utils.token_utils import decode_jwt


def test_decode_jwt_no_token():
    app = Flask(__name__)
    result = decode_jwt(app, None)
    assert result is None


def test_decode_jwt_valid_token():
    app = Flask(__name__)
    secret = 'testsecret'
    app.config['JWT_SECRET_KEY'] = secret

    payload = {'user': {'email': 'u@example.com'}}
    token = pyjwt.encode(payload, secret, algorithm='HS256')
    bearer = f'Bearer {token}'

    result = decode_jwt(app, bearer)
    assert result['user']['email'] == 'u@example.com'


def test_decode_jwt_invalid_signature():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'rightsecret'
    wrong_token = pyjwt.encode({'user': {'email': 'x'}}, 'wrongsecret', algorithm='HS256')

    with pytest.raises(ValueError):
        decode_jwt(app, f'Bearer {wrong_token}')
