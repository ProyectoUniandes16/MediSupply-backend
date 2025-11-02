import pytest
from app.services import ValidationError, ConflictError, NotFoundError


@pytest.fixture
def base_payload(sample_inventario_data):
    """Payload base para crear/actualizar inventarios."""
    return {
        "productoId": sample_inventario_data["productoId"],
        "cantidad": sample_inventario_data["cantidad"],
        "ubicacion": sample_inventario_data["ubicacion"],
    }


def test_crear_inventario_success(client, mocker, sample_inventario_dict, base_payload):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.crear_inventario",
        return_value=sample_inventario_dict,
    )

    response = client.post("/api/inventarios", json=base_payload)

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["id"] == sample_inventario_dict["id"]
    assert payload["productoId"] == base_payload["productoId"]


def test_crear_inventario_validation_error(client, mocker, base_payload):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.crear_inventario",
        side_effect=ValidationError("datos invalidos"),
    )

    response = client.post("/api/inventarios", json=base_payload)

    assert response.status_code == 400
    assert "datos invalidos" in response.get_json()["error"]


def test_crear_inventario_conflict_error(client, mocker, base_payload):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.crear_inventario",
        side_effect=ConflictError("duplicado"),
    )

    response = client.post("/api/inventarios", json=base_payload)

    assert response.status_code == 409
    assert response.get_json()["error"] == "duplicado"


def test_crear_inventario_unexpected_error(client, mocker, base_payload):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.crear_inventario",
        side_effect=RuntimeError("boom"),
    )

    response = client.post("/api/inventarios", json=base_payload)

    assert response.status_code == 500
    assert "Error interno" in response.get_json()["error"]


def test_listar_inventarios_adjusts_limits(client, mocker, sample_inventario_dict):
    service_mock = mocker.patch(
        "app.routes.inventarios.inventarios_service.listar_inventarios",
        return_value=[sample_inventario_dict],
    )

    response = client.get("/api/inventarios?productoId=7&ubicacion=dep&limite=5005&offset=-10")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["limite"] == 1000
    assert payload["offset"] == 0
    service_mock.assert_called_once_with(producto_id="7", ubicacion="dep", limite=1000, offset=0)


def test_listar_inventarios_handles_exception(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.listar_inventarios",
        side_effect=RuntimeError("fallo"),
    )

    response = client.get("/api/inventarios")

    assert response.status_code == 500
    assert "Error interno" in response.get_json()["error"]


def test_obtener_inventario_success(client, mocker, sample_inventario_dict):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.obtener_inventario_por_id",
        return_value=sample_inventario_dict,
    )

    response = client.get("/api/inventarios/abc")

    assert response.status_code == 200
    assert response.get_json()["id"] == sample_inventario_dict["id"]


def test_obtener_inventario_not_found(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.obtener_inventario_por_id",
        side_effect=NotFoundError("no existe"),
    )

    response = client.get("/api/inventarios/absent")

    assert response.status_code == 404
    assert response.get_json()["error"] == "no existe"


def test_actualizar_inventario_success(client, mocker, sample_inventario_dict):
    update_mock = mocker.patch(
        "app.routes.inventarios.inventarios_service.actualizar_inventario",
        return_value=sample_inventario_dict,
    )

    response = client.put("/api/inventarios/id-1", json={"cantidad": 50})

    assert response.status_code == 200
    assert response.get_json()["cantidad"] == sample_inventario_dict["cantidad"]
    update_mock.assert_called_once_with("id-1", {"cantidad": 50})


def test_actualizar_inventario_not_found(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.actualizar_inventario",
        side_effect=NotFoundError("missing"),
    )

    response = client.put("/api/inventarios/not-found", json={})

    assert response.status_code == 404
    assert response.get_json()["error"] == "missing"


def test_actualizar_inventario_validation_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.actualizar_inventario",
        side_effect=ValidationError("bad data"),
    )

    response = client.put("/api/inventarios/id-2", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "bad data"


def test_actualizar_inventario_conflict_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.actualizar_inventario",
        side_effect=ConflictError("dup"),
    )

    response = client.put("/api/inventarios/id-3", json={})

    assert response.status_code == 409
    assert response.get_json()["error"] == "dup"


def test_actualizar_inventario_unexpected_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.actualizar_inventario",
        side_effect=RuntimeError("fallo"),
    )

    response = client.put("/api/inventarios/id-4", json={})

    assert response.status_code == 500
    assert "Error interno" in response.get_json()["error"]


def test_actualizar_parcial_inventario_success(client, mocker, sample_inventario_dict):
    update_mock = mocker.patch(
        "app.routes.inventarios.inventarios_service.actualizar_inventario",
        return_value=sample_inventario_dict,
    )

    response = client.patch("/api/inventarios/id-5", json={"cantidad": 20})

    assert response.status_code == 200
    assert response.get_json()["id"] == sample_inventario_dict["id"]
    update_mock.assert_called_once_with("id-5", {"cantidad": 20})


def test_eliminar_inventario_success(client, mocker):
    delete_mock = mocker.patch(
        "app.routes.inventarios.inventarios_service.eliminar_inventario",
        return_value=None,
    )

    response = client.delete("/api/inventarios/id-1")

    assert response.status_code == 200
    assert response.get_json()["mensaje"].startswith("Inventario eliminado")
    delete_mock.assert_called_once_with("id-1")


def test_eliminar_inventario_not_found(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.eliminar_inventario",
        side_effect=NotFoundError("missing"),
    )

    response = client.delete("/api/inventarios/id-2")

    assert response.status_code == 404
    assert response.get_json()["error"] == "missing"


def test_eliminar_inventario_unexpected_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.eliminar_inventario",
        side_effect=RuntimeError("boom"),
    )

    response = client.delete("/api/inventarios/id-3")

    assert response.status_code == 500
    assert "Error interno" in response.get_json()["error"]


def test_ajustar_cantidad_missing_field(client):
    response = client.post("/api/inventarios/id-1/ajustar", json={"usuario": "tester"})

    assert response.status_code == 400
    assert "ajuste" in response.get_json()["error"]


def test_ajustar_cantidad_non_integer(client):
    response = client.post("/api/inventarios/id-1/ajustar", json={"ajuste": "5"})

    assert response.status_code == 400
    assert "entero" in response.get_json()["error"]


def test_ajustar_cantidad_success(client, mocker, sample_inventario_dict):
    adjust_mock = mocker.patch(
        "app.routes.inventarios.inventarios_service.ajustar_cantidad",
        return_value=sample_inventario_dict,
    )

    response = client.post(
        "/api/inventarios/id-1/ajustar",
        json={"ajuste": 5, "usuario": "tester"},
    )

    assert response.status_code == 200
    assert response.get_json()["id"] == sample_inventario_dict["id"]
    adjust_mock.assert_called_once_with("id-1", 5, "tester")


def test_ajustar_cantidad_not_found(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.ajustar_cantidad",
        side_effect=NotFoundError("sin inventario"),
    )

    response = client.post("/api/inventarios/id-2/ajustar", json={"ajuste": 1})

    assert response.status_code == 404
    assert response.get_json()["error"] == "sin inventario"


def test_ajustar_cantidad_validation_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.ajustar_cantidad",
        side_effect=ValidationError("negativo"),
    )

    response = client.post("/api/inventarios/id-3/ajustar", json={"ajuste": -5})

    assert response.status_code == 400
    assert response.get_json()["error"] == "negativo"


def test_ajustar_cantidad_unexpected_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.ajustar_cantidad",
        side_effect=RuntimeError("fail"),
    )

    response = client.post("/api/inventarios/id-4/ajustar", json={"ajuste": 9})

    assert response.status_code == 500
    assert "Error interno" in response.get_json()["error"]


def test_obtener_inventarios_por_producto_success(client, mocker, sample_inventario_dict):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.listar_inventarios",
        return_value=[sample_inventario_dict],
    )

    response = client.get("/api/inventarios/producto/10")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["productoId"] == "10"
    assert payload["total"] == 1


def test_obtener_inventarios_por_producto_error(client, mocker):
    mocker.patch(
        "app.routes.inventarios.inventarios_service.listar_inventarios",
        side_effect=RuntimeError("fallo"),
    )

    response = client.get("/api/inventarios/producto/99")

    assert response.status_code == 500
    assert "Error interno" in response.get_json()["error"]


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
