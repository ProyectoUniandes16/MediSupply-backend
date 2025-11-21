import json

from app.extensions import db
from app.models.import_job import ImportJob
from app.services.csv_service import CSVImportError
from app.workers import sqs_worker


def test_parse_message_data_variants():
    payload = {"job_id": "123"}
    assert sqs_worker._parse_message_data(json.dumps(payload).encode("utf-8")) == payload
    assert sqs_worker._parse_message_data(payload) == payload
    assert sqs_worker._parse_message_data("{invalid json") is None
    assert sqs_worker._parse_message_data(12345) is None


def test_formatear_error_csv_handles_dict():
    formatted = sqs_worker._formatear_error_csv({"error": "CSV inválido", "codigo": "CSV_VACIO"})
    assert formatted.startswith("{")
    assert "CSV_VACIO" in formatted


def test_aplicar_resultado_job_updates_fields(app):
    with app.app_context():
        job = ImportJob(
            id="job-util-1",
            nombre_archivo="productos.csv",
            usuario_registro="tester",
            total_filas=5
        )
        db.session.add(job)
        db.session.commit()

        sqs_worker._aplicar_resultado_job(job, {
            "exitosos": 3,
            "fallidos": 2,
            "detalles_errores": [{"fila": 1}, {"fila": 2}, {"fila": 3}]
        })

        assert job.estado == "COMPLETADO"
        assert job.exitosos == 3
        assert job.fallidos == 2
        assert job.detalles_errores["errores_capturados"] == 3
        assert "mensaje_finalizacion" in job.extra_metadata


def test_procesar_mensaje_local_success(app, monkeypatch, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("col1\nvalor\n", encoding="utf-8")

    class DummyCSVService:
        def procesar_csv_desde_contenido(self, contenido_csv, usuario_importacion, callback_progreso):
            callback_progreso(1, 1, 1, 0)
            return {"exitosos": 1, "fallidos": 0, "detalles_errores": []}

    monkeypatch.setattr(sqs_worker, "CSVProductoService", lambda: DummyCSVService())
    monkeypatch.setattr(sqs_worker.LocalImportService, "leer_csv", lambda path: csv_path.read_text(encoding="utf-8"))

    with app.app_context():
        job = ImportJob(
            id="job-local-1",
            nombre_archivo="data.csv",
            local_path=str(csv_path),
            usuario_registro="tester",
            estado="EN_COLA",
            total_filas=1
        )
        db.session.add(job)
        db.session.commit()

    payload = {"job_id": "job-local-1", "usuario_registro": "tester", "metadata": {"total_filas": 1}}
    resultado = sqs_worker.procesar_mensaje(app, payload)

    with app.app_context():
        job_refrescado = db.session.get(ImportJob, "job-local-1")
        assert resultado is True
        assert job_refrescado.estado == "COMPLETADO"
        assert job_refrescado.exitosos == 1
        assert job_refrescado.progreso == 100.0


def test_procesar_mensaje_local_csv_error(app, monkeypatch, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("col1\nvalor\n", encoding="utf-8")

    class FailingCSVService:
        def procesar_csv_desde_contenido(self, contenido_csv, usuario_importacion, callback_progreso):
            raise CSVImportError({"error": "CSV inválido", "codigo": "CSV_VACIO"})

    monkeypatch.setattr(sqs_worker, "CSVProductoService", lambda: FailingCSVService())
    monkeypatch.setattr(sqs_worker.LocalImportService, "leer_csv", lambda path: csv_path.read_text(encoding="utf-8"))

    with app.app_context():
        job = ImportJob(
            id="job-local-2",
            nombre_archivo="data.csv",
            local_path=str(csv_path),
            usuario_registro="tester",
            estado="EN_COLA"
        )
        db.session.add(job)
        db.session.commit()

    resultado = sqs_worker.procesar_mensaje(app, {"job_id": "job-local-2"})

    with app.app_context():
        job_refrescado = db.session.get(ImportJob, "job-local-2")
        assert resultado is False
        assert job_refrescado.estado == "FALLIDO"
        assert "CSV inválido" in job_refrescado.mensaje_error


def test_procesar_mensaje_invalid_payload(app):
    assert sqs_worker.procesar_mensaje(app, "no es json") is False
    assert sqs_worker.procesar_mensaje(app, 12345) is False


def test_procesar_mensaje_sqs_success(app, monkeypatch, tmp_path):
    class DummyCSVService:
        def procesar_csv_desde_contenido(self, contenido_csv, usuario_importacion, callback_progreso):
            callback_progreso(2, 2, 2, 0)
            return {"exitosos": 2, "fallidos": 0, "detalles_errores": []}

    class FakeSQSService:
        def __init__(self):
            self.deleted_messages = []

        def eliminar_mensaje(self, message):
            self.deleted_messages.append(message)

        def cambiar_visibilidad_mensaje(self, *args, **kwargs):
            return True

    class FakeS3Service:
        def __init__(self, contenido):
            self.contenido = contenido

        def descargar_csv(self, s3_key):
            return self.contenido

    monkeypatch.setattr(sqs_worker, "CSVProductoService", lambda: DummyCSVService())

    with app.app_context():
        job = ImportJob(
            id="job-sqs-1",
            nombre_archivo="s3.csv",
            usuario_registro="tester",
            estado="EN_COLA"
        )
        db.session.add(job)
        db.session.commit()

    message_body = {
        "job_id": "job-sqs-1",
        "s3_key": "imports/test.csv",
        "usuario_registro": "tester",
        "metadata": {"total_filas": 2}
    }
    message = {
        "Body": json.dumps(message_body),
        "MessageId": "msg-1",
        "ReceiptHandle": "handle-1"
    }

    fake_sqs = FakeSQSService()
    fake_s3 = FakeS3Service("col1\nvalor\n")

    resultado = sqs_worker.procesar_mensaje(app, message, fake_sqs, fake_s3)

    with app.app_context():
        job_refrescado = db.session.get(ImportJob, "job-sqs-1")
        assert resultado is True
        assert job_refrescado.estado == "COMPLETADO"
        assert job_refrescado.exitosos == 2
        assert job_refrescado.total_filas == 2
        assert fake_sqs.deleted_messages
