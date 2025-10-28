"""Pruebas de integración para validar el Redis Service en ejecución real."""

import os
import uuid

import pytest
import requests


pytestmark = pytest.mark.integration

DEFAULT_BASE_URL = "http://localhost:5011"
REQUEST_TIMEOUT = int(os.getenv("REDIS_SERVICE_TIMEOUT", "5"))


@pytest.fixture(scope="module")
def base_url():
    """URL base del servicio a probar."""
    return os.getenv("REDIS_SERVICE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture(scope="module")
def http_session():
    """Sesion HTTP reutilizable para reducir overhead en las peticiones."""
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def service_ready(base_url):
    """Verifica que el servicio esté disponible antes de ejecutar las pruebas."""
    try:
        response = requests.get(f"{base_url}/health", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except Exception as exc:
        pytest.skip(f"redis_service no disponible en {base_url}: {exc}")


def _unique_key(prefix: str) -> str:
    """Genera claves únicas para evitar colisiones entre pruebas."""
    return f"tests:{prefix}:{uuid.uuid4().hex}"


@pytest.mark.integration
def test_health_endpoint(base_url, http_session, service_ready):
    response = http_session.get(f"{base_url}/health", timeout=REQUEST_TIMEOUT)

    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("application/json")

    data = response.json()
    assert data["service"] == "redis_service"
    assert data["status"] == "healthy"
    assert data["redis"] == "connected"
    assert data["port"] == 5011


@pytest.mark.integration
def test_cache_crud_flow(base_url, http_session, service_ready):
    key = _unique_key("cache")
    value = {"producto": 123, "cantidad": 45, "ubicacion": "A1"}
    ttl = 120

    try:
        create_resp = http_session.post(
            f"{base_url}/api/cache/",
            json={"key": key, "value": value, "ttl": ttl},
            timeout=REQUEST_TIMEOUT,
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["key"] == key

        fetch_resp = http_session.get(
            f"{base_url}/api/cache/{key}", timeout=REQUEST_TIMEOUT
        )
        assert fetch_resp.status_code == 200
        body = fetch_resp.json()
        assert body["key"] == key
        assert body["value"] == value
        assert body["ttl"] >= -1
        assert body["ttl"] <= ttl

        exists_resp = http_session.get(
            f"{base_url}/api/cache/exists/{key}", timeout=REQUEST_TIMEOUT
        )
        assert exists_resp.status_code == 200
        assert exists_resp.json()["exists"] is True

    except :
        pattern_prefix = ":".join(key.split(":")[:-1])
        list_resp = http_session.get(
            f"{base_url}/api/cache/keys",
            params={"pattern": f"{pattern_prefix}:*"},
            timeout=REQUEST_TIMEOUT,
        )
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert list_body["count"] >= 1
        assert key in list_body["keys"]
    finally:
        delete_resp = http_session.delete(
            f"{base_url}/api/cache/{key}", timeout=REQUEST_TIMEOUT
        )
        assert delete_resp.status_code in (200, 404)

    missing_resp = http_session.get(
        f"{base_url}/api/cache/{key}", timeout=REQUEST_TIMEOUT
    )
    assert missing_resp.status_code == 404


@pytest.mark.integration
def test_cache_pattern_deletion(base_url, http_session, service_ready):
    prefix = _unique_key("pattern")
    keys = [f"{prefix}:{suffix}" for suffix in ("a", "b", "c")]

    for key in keys:
        create_resp = http_session.post(
            f"{base_url}/api/cache/",
            json={"key": key, "value": {"key": key}, "ttl": 300},
            timeout=REQUEST_TIMEOUT,
        )
        assert create_resp.status_code == 201

    delete_resp = http_session.delete(
        f"{base_url}/api/cache/pattern/{prefix}:*",
        timeout=REQUEST_TIMEOUT,
    )
    assert delete_resp.status_code == 200
    deleted = delete_resp.json()["deleted_count"]
    assert deleted >= len(keys)

    verify_resp = http_session.get(
        f"{base_url}/api/cache/keys",
        params={"pattern": f"{prefix}:*"},
        timeout=REQUEST_TIMEOUT,
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["count"] == 0


@pytest.mark.integration
def test_queue_publish_and_subscribers(base_url, http_session, service_ready):
    channel = _unique_key("queue")
    message = {"evento": "update", "producto": 99}

    publish_resp = http_session.post(
        f"{base_url}/api/queue/publish",
        json={"channel": channel, "message": message},
        timeout=REQUEST_TIMEOUT,
    )
    assert publish_resp.status_code == 200
    publish_body = publish_resp.json()
    assert publish_body["channel"] == channel
    assert isinstance(publish_body["subscribers"], int)

    subscribers_resp = http_session.get(
        f"{base_url}/api/queue/subscribers/{channel}", timeout=REQUEST_TIMEOUT
    )
    assert subscribers_resp.status_code == 200
    subs_body = subscribers_resp.json()
    assert subs_body["channel"] == channel
    assert isinstance(subs_body["subscribers"], int)
    assert subs_body["subscribers"] >= 0

    channels_resp = http_session.get(
        f"{base_url}/api/queue/channels", timeout=REQUEST_TIMEOUT
    )
    assert channels_resp.status_code == 200
    channels_body = channels_resp.json()
    assert "pattern" in channels_body
    assert "channels" in channels_body
    assert isinstance(channels_body["channels"], list)
    for item in channels_body["channels"]:
        assert "channel" in item
        assert "subscribers" in item


@pytest.mark.integration
def test_stats_endpoint(base_url, http_session, service_ready):
    stats_resp = http_session.get(f"{base_url}/stats", timeout=REQUEST_TIMEOUT)
    assert stats_resp.status_code == 200

    data = stats_resp.json()
    assert data.get("status") == "connected"
    for field in ("redis_version", "connected_clients", "used_memory_human"):
        assert field in data
