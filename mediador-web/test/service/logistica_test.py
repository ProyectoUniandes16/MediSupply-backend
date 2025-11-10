import pytest
from unittest.mock import MagicMock, patch
import requests
from flask import Flask

from src.services.logistica import crear_visita_logistica, LogisticaServiceError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


def _payload():
    return {
        "cliente_id": 10,
        "vendedor_id": "ven-10",
        "fecha_visita": "2025-11-10",
    }


@patch("src.services.logistica.requests.post")
def test_crear_visita_logistica_exito(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": 1, "estado": "pendiente"}
    mock_post.return_value = mock_response

    resultado = crear_visita_logistica(_payload(), headers={"Authorization": "Bearer token"})

    assert resultado["id"] == 1
    mock_post.assert_called_once_with(
        "http://localhost:5013/visitas",
        json=_payload(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer token"},
        timeout=10,
    )


def test_crear_visita_logistica_payload_invalido():
    with pytest.raises(LogisticaServiceError) as exc:
        crear_visita_logistica(None)

    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "DATOS_VACIOS"


def test_crear_visita_logistica_campos_faltantes():
    with pytest.raises(LogisticaServiceError) as exc:
        crear_visita_logistica({"cliente_id": 1})

    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "CAMPOS_FALTANTES"


@patch("src.services.logistica.requests.post")
def test_crear_visita_logistica_http_error(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_response.text = "Duplicada"
    mock_response.json.return_value = {"error": "Duplicada"}
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_post.return_value = mock_response

    with pytest.raises(LogisticaServiceError) as exc:
        crear_visita_logistica(_payload())

    assert exc.value.status_code == 409
    assert exc.value.message["error"] == "Duplicada"


@patch("src.services.logistica.requests.post")
def test_crear_visita_logistica_http_error_sin_json(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal"
    mock_response.json.side_effect = ValueError("invalid json")
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_post.return_value = mock_response

    with pytest.raises(LogisticaServiceError) as exc:
        crear_visita_logistica(_payload())

    assert exc.value.status_code == 500
    assert exc.value.message["codigo"] == "ERROR_HTTP"


@patch("src.services.logistica.requests.post")
def test_crear_visita_logistica_conexion_error(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectionError("fail")

    with pytest.raises(LogisticaServiceError) as exc:
        crear_visita_logistica(_payload())

    assert exc.value.status_code == 503
    assert exc.value.message["codigo"] == "ERROR_CONEXION"


@patch("src.services.logistica.requests.post")
def test_crear_visita_logistica_respuesta_invalida(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("invalid")
    mock_post.return_value = mock_response

    with pytest.raises(LogisticaServiceError) as exc:
        crear_visita_logistica(_payload())

    assert exc.value.status_code == 502
    assert exc.value.message["codigo"] == "RESPUESTA_INVALIDA"


@patch("src.services.logistica.requests.post")
def test_crear_visita_logistica_env_personalizado(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": 10}
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"LOGISTICA_URL": "http://logi:9000"}):
        crear_visita_logistica(_payload())

    mock_post.assert_called_once_with(
        "http://logi:9000/visitas",
        json=_payload(),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
