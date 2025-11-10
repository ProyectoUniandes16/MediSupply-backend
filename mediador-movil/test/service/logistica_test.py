import pytest
from unittest.mock import MagicMock, patch
import requests
from flask import Flask

from src.services.logistica import actualizar_visita_logistica, LogisticaServiceError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


def _payload(**overrides):
    base = {"estado": "pendiente", "comentarios": "  texto  "}
    base.update(overrides)
    return base


@patch("src.services.logistica.requests.patch")
def test_actualizar_visita_logistica_exito(mock_patch):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": 5, "estado": "pendiente"}
    mock_patch.return_value = mock_response

    resultado = actualizar_visita_logistica(5, _payload(), headers={"Authorization": "Bearer token"})

    assert resultado["id"] == 5
    mock_patch.assert_called_once_with(
        "http://localhost:5013/visitas/5",
        json={"estado": "pendiente", "comentarios": "texto"},
        headers={"Content-Type": "application/json", "Authorization": "Bearer token"},
        timeout=10,
    )


def test_actualizar_visita_logistica_id_invalido():
    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(0, _payload())
    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "VISITA_ID_INVALIDO"


def test_actualizar_visita_logistica_payload_vacio():
    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(1, None)
    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "DATOS_VACIOS"


def test_actualizar_visita_logistica_estado_faltante():
    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(1, {"comentarios": "x"})
    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "ESTADO_REQUERIDO"


def test_actualizar_visita_logistica_estado_invalido():
    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(1, {"estado": "cancelado"})
    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "ESTADO_INVALIDO"


def test_actualizar_visita_logistica_comentarios_invalidos():
    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(1, {"estado": "pendiente", "comentarios": 123})
    assert exc.value.status_code == 400
    assert exc.value.message["codigo"] == "COMENTARIOS_INVALIDOS"


@patch("src.services.logistica.requests.patch")
def test_actualizar_visita_logistica_http_error(mock_patch):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "No encontrada"
    mock_response.json.return_value = {"error": "No encontrada"}
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_patch.return_value = mock_response

    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(1, _payload())

    assert exc.value.status_code == 404
    assert exc.value.message["error"] == "No encontrada"


@patch("src.services.logistica.requests.patch")
def test_actualizar_visita_logistica_http_error_sin_json(mock_patch):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal"
    mock_response.json.side_effect = ValueError("invalid json")
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_patch.return_value = mock_response

    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(2, _payload())

    assert exc.value.status_code == 500
    assert exc.value.message["codigo"] == "ERROR_HTTP"


@patch("src.services.logistica.requests.patch")
def test_actualizar_visita_logistica_conexion_error(mock_patch):
    mock_patch.side_effect = requests.exceptions.ConnectionError("fallo")

    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(2, _payload())

    assert exc.value.status_code == 503
    assert exc.value.message["codigo"] == "ERROR_CONEXION"


@patch("src.services.logistica.requests.patch")
def test_actualizar_visita_logistica_respuesta_invalida(mock_patch):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("invalid")
    mock_patch.return_value = mock_response

    with pytest.raises(LogisticaServiceError) as exc:
        actualizar_visita_logistica(2, _payload())

    assert exc.value.status_code == 502
    assert exc.value.message["codigo"] == "RESPUESTA_INVALIDA"


@patch("src.services.logistica.requests.patch")
def test_actualizar_visita_logistica_entorno_personalizado(mock_patch):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": 9}
    mock_patch.return_value = mock_response

    with patch.dict("os.environ", {"LOGISTICA_URL": "http://logi:8000"}):
        actualizar_visita_logistica(9, _payload(comentarios=None))

    mock_patch.assert_called_once_with(
        "http://logi:8000/visitas/9",
        json={"estado": "pendiente", "comentarios": None},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
