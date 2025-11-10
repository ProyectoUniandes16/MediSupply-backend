import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.blueprints.logistica import logistica_bp
from src.services.logistica import LogisticaServiceError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(logistica_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity="usuario-test")


@patch("src.blueprints.logistica.crear_visita_logistica")
def test_crear_visita_logistica_exito(mock_crear, client, access_token):
    mock_crear.return_value = {"id": 1, "cliente_id": 10, "estado": "pendiente"}
    payload = {
        "cliente_id": 10,
        "vendedor_id": "ven-1",
        "fecha_visita": "2025-11-10",
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/visitas", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.get_json()["id"] == 1
    args, kwargs = mock_crear.call_args
    assert args[0] == payload
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")


@patch("src.blueprints.logistica.crear_visita_logistica")
def test_crear_visita_logistica_error_servicio(mock_crear, client, access_token):
    error = LogisticaServiceError({"error": "Duplicada"}, 409)
    mock_crear.side_effect = error

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post(
        "/visitas",
        json={"cliente_id": 99, "vendedor_id": "ven", "fecha_visita": "2025-01-01"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "Duplicada"


@patch("src.blueprints.logistica.crear_visita_logistica")
def test_crear_visita_logistica_error_inesperado(mock_crear, client, access_token, app):
    mock_crear.side_effect = RuntimeError("boom")
    mock_logger = MagicMock()

    with app.app_context():
        with patch("src.blueprints.logistica.current_app") as mock_current_app:
            mock_current_app.logger = mock_logger
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.post(
                "/visitas",
                json={"cliente_id": 1, "vendedor_id": "v-1", "fecha_visita": "2025-01-01"},
                headers=headers,
            )

    assert response.status_code == 500
    assert response.get_json()["codigo"] == "ERROR_INTERNO_SERVIDOR"
    mock_logger.error.assert_called_once()


def test_crear_visita_logistica_sin_token(client):
    response = client.post(
        "/visitas",
        json={"cliente_id": 1, "vendedor_id": "v-1", "fecha_visita": "2025-01-01"},
    )
    assert response.status_code == 401
