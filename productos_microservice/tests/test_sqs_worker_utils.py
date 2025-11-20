import importlib
import json
import signal

from app.extensions import db
from app.models.import_job import ImportJob
from app.workers import sqs_worker


def test_signal_handler_activa_shutdown(monkeypatch):
    importlib.reload(sqs_worker)
    sqs_worker.shutdown_requested = False
    sqs_worker.signal_handler(signal.SIGTERM, None)
    assert sqs_worker.shutdown_requested is True


def test_parse_message_data_bytes():
    payload = {'job_id': 'job-1'}
    resultado = sqs_worker._parse_message_data(json.dumps(payload).encode('utf-8'))
    assert resultado == payload


def test_parse_message_data_invalido():
    resultado = sqs_worker._parse_message_data(b'not-json')
    assert resultado is None


def test_formatear_error_csv_devuelve_json():
    error = {'error': 'CSV inválido', 'codigo': 'CSV_VACIO'}
    resultado = sqs_worker._formatear_error_csv(error)
    assert json.loads(resultado) == error


def test_aplicar_resultado_job_actualiza_campos(app):
    with app.app_context():
        job = ImportJob(
            id='job-test',
            nombre_archivo='import.csv',
            usuario_registro='tester@example.com',
            total_filas=5
        )
        db.session.add(job)
        db.session.commit()

        resultado = {
            'exitosos': 3,
            'fallidos': 2,
            'detalles_errores': [{'fila': 2, 'error': 'Duplicado'}]
        }

        sqs_worker._aplicar_resultado_job(job, resultado)

        assert job.estado == 'COMPLETADO'
        assert job.exitosos == 3
        assert job.fallidos == 2
        assert job.detalles_errores['total_errores'] == 2
        assert job.detalles_errores['errores_capturados'] == 1
        assert job.detalles_errores['errores'][0]['fila'] == 2
