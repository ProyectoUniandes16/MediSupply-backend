from src.services.visita_vendedor_service import VisitaVendedorServiceError
import src.blueprints.visitas as visitas_blueprint


def test_crear_visita_vendedor_endpoint_success(client, access_token, monkeypatch):
    payload = {
        "cliente_id": 20,
        "vendedor_id": "v-20",
        "fecha_visita": "2025-10-12",
    }
    esperado = {
        "id": 1,
        **payload,
        "estado": "pendiente",
        "comentarios": None,
    }

    monkeypatch.setattr(
        visitas_blueprint,
        "crear_visita_vendedor",
        lambda data: esperado,
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/visitas", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.get_json() == esperado


def test_crear_visita_vendedor_endpoint_service_error(client, access_token, monkeypatch):
    error = VisitaVendedorServiceError({"error": "duplicado"}, 409)

    def raise_error(_data):
        raise error

    monkeypatch.setattr(visitas_blueprint, "crear_visita_vendedor", raise_error)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/visitas", json={}, headers=headers)

    assert response.status_code == 409
    assert response.get_json() == {"error": "duplicado"}


def test_crear_visita_vendedor_endpoint_unexpected_error(client, access_token, monkeypatch):
    def raise_exc(_data):
        raise RuntimeError("boom")

    monkeypatch.setattr(visitas_blueprint, "crear_visita_vendedor", raise_exc)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/visitas", json={}, headers=headers)

    assert response.status_code == 500
    body = response.get_json()
    assert body.get("codigo") == "ERROR_INTERNO_SERVIDOR"


def test_actualizar_visita_vendedor_endpoint_success(client, access_token, monkeypatch):
    esperado = {
        "id": 5,
        "cliente_id": 99,
        "vendedor_id": "v-99",
        "estado": "finalizado",
        "comentarios": "Visita exitosa",
    }

    monkeypatch.setattr(
        visitas_blueprint,
        "actualizar_visita_vendedor",
        lambda visita_id, data: esperado,
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.patch(
    "/visitas/5",
        json={"estado": "finalizado", "comentarios": "Visita exitosa"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.get_json() == esperado


def test_actualizar_visita_vendedor_endpoint_service_error(client, access_token, monkeypatch):
    error = VisitaVendedorServiceError({"error": "no encontrada"}, 404)

    def raise_error(_visita_id, _data):
        raise error

    monkeypatch.setattr(visitas_blueprint, "actualizar_visita_vendedor", raise_error)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.patch(
    "/visitas/123",
        json={"estado": "finalizado"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "no encontrada"}


def test_actualizar_visita_vendedor_endpoint_unexpected_error(client, access_token, monkeypatch):
    def raise_exc(_visita_id, _data):
        raise RuntimeError("boom")

    monkeypatch.setattr(visitas_blueprint, "actualizar_visita_vendedor", raise_exc)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.patch(
    "/visitas/8",
        json={"estado": "en progreso"},
        headers=headers,
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body.get("codigo") == "ERROR_INTERNO_SERVIDOR"
