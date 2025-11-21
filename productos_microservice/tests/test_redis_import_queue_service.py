import requests

from app.services.redis_import_queue_service import RedisImportQueueService


class DummySuccessResponse:
    status_code = 200
    text = "OK"

    def json(self):
        return {"status": "published"}


class DummyFailureResponse:
    status_code = 500
    text = "Internal Error"

    def json(self):
        return {"status": "error"}


def test_publicar_import_job_exitoso(monkeypatch):
    payload_capture = {}

    def fake_post(url, json, timeout):
        payload_capture["url"] = url
        payload_capture["json"] = json
        payload_capture["timeout"] = timeout
        return DummySuccessResponse()

    monkeypatch.setenv('REDIS_SERVICE_URL', 'http://redis-service/')
    monkeypatch.setenv('REDIS_IMPORT_CHANNEL', 'import-channel')
    monkeypatch.setattr(requests, 'post', fake_post)

    resultado = RedisImportQueueService.publicar_import_job(
        job_id='job-1',
        local_path='/tmp/job.csv',
        nombre_archivo='job.csv',
        usuario_registro='tester@example.com',
        metadata={'total_filas': 10}
    )

    assert resultado is True
    assert payload_capture["url"] == 'http://redis-service/api/queue/publish'
    assert payload_capture["json"]["channel"] == 'import-channel'
    assert payload_capture["json"]["message"]["job_id"] == 'job-1'


def test_publicar_import_job_falla(monkeypatch):
    monkeypatch.setenv('REDIS_SERVICE_URL', 'http://redis-service')

    def fake_post(url, json, timeout):
        return DummyFailureResponse()

    monkeypatch.setattr(requests, 'post', fake_post)

    resultado = RedisImportQueueService.publicar_import_job(
        job_id='job-1',
        local_path='/tmp/job.csv',
        nombre_archivo='job.csv',
        usuario_registro='tester@example.com'
    )

    assert resultado is False


def test_publicar_import_job_excepcion(monkeypatch):
    monkeypatch.setenv('REDIS_SERVICE_URL', 'http://redis-service')

    def fake_post(url, json, timeout):
        raise requests.RequestException("connection error")

    monkeypatch.setattr(requests, 'post', fake_post)

    resultado = RedisImportQueueService.publicar_import_job(
        job_id='job-1',
        local_path='/tmp/job.csv',
        nombre_archivo='job.csv',
        usuario_registro='tester@example.com'
    )

    assert resultado is False
