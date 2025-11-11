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
        return create_access_token(identity="user-test")


@patch("src.blueprints.logistica.actualizar_visita_logistica")
def test_actualizar_visita_logistica_exito(mock_actualizar, client, access_token):
    mock_actualizar.return_value = {"id": 5, "estado": "finalizado"}
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"estado": "finalizado", "comentarios": "Visita ok"}

    response = client.patch("/visitas/5", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.get_json()["estado"] == "finalizado"
    args, kwargs = mock_actualizar.call_args
    assert args[0] == 5
    assert args[1] == payload
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")


@patch("src.blueprints.logistica.actualizar_visita_logistica")
def test_actualizar_visita_logistica_error_controlado(mock_actualizar, client, access_token):
    error = LogisticaServiceError({"error": "No encontrada"}, 404)
    mock_actualizar.side_effect = error

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.patch(
        "/visitas/9",
        json={"estado": "en progreso"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "No encontrada"


@patch("src.blueprints.logistica.actualizar_visita_logistica")
def test_actualizar_visita_logistica_error_inesperado(mock_actualizar, client, access_token, app):
    mock_actualizar.side_effect = RuntimeError("boom")
    mock_logger = MagicMock()

    with app.app_context():
        with patch("src.blueprints.logistica.current_app") as mock_current_app:
            mock_current_app.logger = mock_logger
            mock_current_app.config = {
                "JWT_SECRET_KEY": "test-secret",
                "JWT_ALGORITHM": "HS256",
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.patch(
                "/visitas/1",
                json={"estado": "pendiente"},
                headers=headers,
            )

    assert response.status_code == 500
    assert response.get_json()["codigo"] == "ERROR_INTERNO_SERVIDOR"
    mock_logger.error.assert_called_once()


def test_actualizar_visita_logistica_sin_token(client):
    response = client.patch("/visitas/3", json={"estado": "pendiente"})
    assert response.status_code == 401


@patch("src.blueprints.logistica.listar_visitas_logistica")
def test_listar_visitas_logistica_exito(mock_listar, client, access_token):
    mock_listar.return_value = {"visitas": []}
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/visitas?vendedor_id=filtro", headers=headers)

    assert response.status_code == 200
    assert response.get_json() == {"visitas": []}
    args, kwargs = mock_listar.call_args
    assert "filtros" in kwargs
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    assert kwargs["vendedor_email"] == "user-test"


@patch("src.blueprints.logistica.listar_visitas_logistica")
def test_listar_visitas_logistica_error_controlado(mock_listar, client, access_token):
    error = LogisticaServiceError({"error": "fallo"}, 400)
    mock_listar.side_effect = error

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/visitas", headers=headers)

    assert response.status_code == 400
    assert response.get_json()["error"] == "fallo"


@patch("src.blueprints.logistica.listar_visitas_logistica")
def test_listar_visitas_logistica_error_inesperado(mock_listar, client, access_token, app):
    mock_listar.side_effect = RuntimeError("boom")
    mock_logger = MagicMock()

    with app.app_context():
        with patch("src.blueprints.logistica.current_app") as mock_current_app:
            mock_current_app.logger = mock_logger
            mock_current_app.config = {
                "JWT_SECRET_KEY": "test-secret",
                "JWT_ALGORITHM": "HS256",
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/visitas", headers=headers)

    assert response.status_code == 500
    assert response.get_json()["codigo"] == "ERROR_INTERNO_SERVIDOR"
    mock_logger.error.assert_called_once()


def test_listar_visitas_logistica_sin_token(client):
    response = client.get("/visitas")
    assert response.status_code == 401


@patch("src.blueprints.logistica.decode_jwt")
def test_listar_visitas_logistica_token_invalido(mock_decode, client, access_token):
    mock_decode.side_effect = ValueError("Token inválido")
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/visitas", headers=headers)

    assert response.status_code == 401
    body = response.get_json()
    assert body["codigo"] == "TOKEN_INVALIDO"
