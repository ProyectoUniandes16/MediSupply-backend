import pytest


@pytest.fixture(autouse=True)
def disable_external_requests(monkeypatch):
    """Evita que los tests hagan llamadas HTTP reales.

    Por defecto reemplaza requests.get/post/put por una función que lanza
    RequestException. Los tests que necesiten simular respuestas deben
    sobrescribirlo con `monkeypatch.setattr(...)` en su propio scope.
    """
    import requests as _requests

    def _raise(*a, **kw):
        raise _requests.exceptions.RequestException("External HTTP calls disabled in tests")

    monkeypatch.setattr(_requests, "get", _raise)
    monkeypatch.setattr(_requests, "post", _raise)
    monkeypatch.setattr(_requests, "put", _raise)
    # también bloquear otros métodos por seguridad
    monkeypatch.setattr(_requests, "delete", _raise)
    monkeypatch.setattr(_requests, "patch", _raise)

    yield
