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


# Tests para optimización de rutas


@patch("src.blueprints.logistica.optimizar_ruta")
def test_optimizar_ruta_exito_formato_json(mock_optimizar, client, access_token):
    """Test de optimización de ruta exitosa con formato JSON"""
    mock_optimizar.return_value = {
        "orden_optimo": [
            {"job_id": "inicio/fin", "ubicacion": [-74.08175, 4.60971]},
            {"job_id": 1, "ubicacion": [-74.0445, 4.676]},
            {"job_id": 2, "ubicacion": [-74.1475, 4.6165]},
        ],
        "resumen": {
            "distancia_total_metros": 25000,
            "tiempo_total_segundos": 1800,
        },
        "mensaje": "Ruta optimizada exitosamente",
    }
    
    payload = {
        "bodega": [-74.08175, 4.60971],
        "destinos": [[-74.0445, 4.676], [-74.1475, 4.6165]],
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/ruta-optima", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert "orden_optimo" in data
    assert "resumen" in data
    assert data["resumen"]["distancia_total_metros"] == 25000
    
    # Verificar que se llamó con los parámetros correctos
    args, kwargs = mock_optimizar.call_args
    assert args[0] == payload
    assert kwargs["formato"] == "json"


@patch("src.blueprints.logistica.optimizar_ruta")
def test_optimizar_ruta_exito_formato_html(mock_optimizar, client, access_token):
    """Test de optimización de ruta exitosa con formato HTML"""
    mock_optimizar.return_value = "<html><body>Mapa de Ruta</body></html>"
    
    payload = {
        "bodega": [-74.08175, 4.60971],
        "destinos": [[-74.0445, 4.676]],
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post(
        "/ruta-optima?formato=html",
        json=payload,
        headers=headers,
    )
    
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert b"Mapa de Ruta" in response.data
    
    # Verificar que se llamó con formato HTML
    args, kwargs = mock_optimizar.call_args
    assert kwargs["formato"] == "html"


@patch("src.blueprints.logistica.optimizar_ruta")
def test_optimizar_ruta_sin_bodega(mock_optimizar, client, access_token):
    """Test sin coordenadas de bodega"""
    error = LogisticaServiceError(
        {"error": "Campo 'bodega' es requerido", "codigo": "BODEGA_REQUERIDA"},
        400,
    )
    mock_optimizar.side_effect = error
    
    payload = {"destinos": [[-74.0445, 4.676]]}
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/ruta-optima", json=payload, headers=headers)
    
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["codigo"] == "BODEGA_REQUERIDA"


@patch("src.blueprints.logistica.optimizar_ruta")
def test_optimizar_ruta_sin_destinos(mock_optimizar, client, access_token):
    """Test sin destinos"""
    error = LogisticaServiceError(
        {"error": "Campo 'destinos' es requerido", "codigo": "DESTINOS_REQUERIDOS"},
        400,
    )
    mock_optimizar.side_effect = error
    
    payload = {"bodega": [-74.08175, 4.60971]}
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/ruta-optima", json=payload, headers=headers)
    
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["codigo"] == "DESTINOS_REQUERIDOS"


@patch("src.blueprints.logistica.optimizar_ruta")
def test_optimizar_ruta_error_servicio(mock_optimizar, client, access_token):
    """Test cuando el servicio retorna error"""
    error = LogisticaServiceError(
        {"error": "Error en API de rutas", "codigo": "ERROR_API"},
        503,
    )
    mock_optimizar.side_effect = error
    
    payload = {
        "bodega": [-74.08175, 4.60971],
        "destinos": [[-74.0445, 4.676]],
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/ruta-optima", json=payload, headers=headers)
    
    assert response.status_code == 503
    data = response.get_json()
    assert data["codigo"] == "ERROR_API"


@patch("src.blueprints.logistica.optimizar_ruta")
def test_optimizar_ruta_error_inesperado(mock_optimizar, client, access_token, app):
    """Test cuando ocurre un error inesperado"""
    mock_optimizar.side_effect = RuntimeError("Error inesperado")
    mock_logger = MagicMock()
    
    with app.app_context():
        with patch("src.blueprints.logistica.current_app") as mock_current_app:
            mock_current_app.logger = mock_logger
            
            payload = {
                "bodega": [-74.08175, 4.60971],
                "destinos": [[-74.0445, 4.676]],
            }
            
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.post("/ruta-optima", json=payload, headers=headers)
    
    assert response.status_code == 500
    data = response.get_json()
    assert data["codigo"] == "ERROR_INTERNO_SERVIDOR"
    mock_logger.error.assert_called_once()


def test_optimizar_ruta_sin_token(client):
    """Test sin token de autenticación"""
    payload = {
        "bodega": [-74.08175, 4.60971],
        "destinos": [[-74.0445, 4.676]],
    }
    
    response = client.post("/ruta-optima", json=payload)
    assert response.status_code == 401
