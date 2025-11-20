"""Tests para el worker de importación basado en Redis"""
from pathlib import Path
from unittest.mock import patch

import pytest

from app import create_app
from app.extensions import db
from app.models.import_job import ImportJob
from app.workers.sqs_worker import procesar_mensaje
from app.services.csv_service import CSVImportError


@pytest.fixture
def app_worker(monkeypatch, tmp_path):
    monkeypatch.setenv('TESTING', 'true')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    app = create_app()
    app.config.from_object('app.config.TestingConfig')
    app.config['UPLOAD_FOLDER'] = tmp_path.as_posix()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csv_local_file(tmp_path: Path) -> str:
    contenido = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id\nProducto Demo,SKU-DEMO-1,Analgésicos,12.5,Frío,2025-12-31,1\n"""
    archivo = tmp_path / "import.csv"
    archivo.write_text(contenido, encoding='utf-8')
    return str(archivo)


class TestRedisWorker:
    def test_procesar_mensaje_exitoso(self, app_worker, csv_local_file):
        with app_worker.app_context():
            job = ImportJob(
                id='job-1',
                nombre_archivo='import.csv',
                local_path=csv_local_file,
                total_filas=1,
                usuario_registro='tester@demo.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()

            payload = {
                'job_id': job.id,
                'local_path': csv_local_file,
                'usuario_registro': 'tester@demo.com',
                'metadata': {'total_filas': 1}
            }

            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                instance = MockCSV.return_value
                instance.procesar_csv_desde_contenido.return_value = {
                    'exitosos': 1,
                    'fallidos': 0,
                    'detalles_errores': []
                }

                resultado = procesar_mensaje(app_worker, payload)

            assert resultado is True
            db.session.refresh(job)
            assert job.estado == 'COMPLETADO'
            assert job.exitosos == 1
            assert job.fallidos == 0
            assert job.progreso == 100.0

    def test_procesar_mensaje_guarda_errores(self, app_worker, csv_local_file):
        with app_worker.app_context():
            job = ImportJob(
                id='job-2',
                nombre_archivo='import.csv',
                local_path=csv_local_file,
                total_filas=2,
                usuario_registro='tester@demo.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()

            payload = {
                'job_id': job.id,
                'local_path': csv_local_file,
                'usuario_registro': 'tester@demo.com',
                'metadata': {'total_filas': 2}
            }

            errores = [
                {'fila': 2, 'sku': 'SKU-1', 'error': 'Duplicado', 'codigo': 'SKU_DUPLICADO'}
            ]

            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                instance = MockCSV.return_value
                instance.procesar_csv_desde_contenido.return_value = {
                    'exitosos': 1,
                    'fallidos': 1,
                    'detalles_errores': errores
                }

                resultado = procesar_mensaje(app_worker, payload)

            assert resultado is True
            db.session.refresh(job)
            assert job.estado == 'COMPLETADO'
            assert job.fallidos == 1
            assert job.detalles_errores['total_errores'] == 1
            assert job.detalles_errores['errores'][0]['sku'] == 'SKU-1'

    def test_procesar_mensaje_job_no_encontrado(self, app_worker, csv_local_file):
        payload = {
            'job_id': 'no-existe',
            'local_path': csv_local_file
        }
        assert procesar_mensaje(app_worker, payload) is False

    def test_procesar_mensaje_archivo_missing(self, app_worker):
        with app_worker.app_context():
            job = ImportJob(
                id='job-3',
                nombre_archivo='import.csv',
                local_path='/tmp/no_existe.csv',
                total_filas=1,
                usuario_registro='tester@demo.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()

            payload = {
                'job_id': job.id,
                'local_path': '/tmp/no_existe.csv'
            }

            resultado = procesar_mensaje(app_worker, payload)
            assert resultado is False
            db.session.refresh(job)
            assert job.estado == 'FALLIDO'

    def test_procesar_mensaje_csv_error(self, app_worker, csv_local_file):
        with app_worker.app_context():
            job = ImportJob(
                id='job-4',
                nombre_archivo='import.csv',
                local_path=csv_local_file,
                total_filas=1,
                usuario_registro='tester@demo.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()

            payload = {
                'job_id': job.id,
                'local_path': csv_local_file
            }

            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                instance = MockCSV.return_value
                instance.procesar_csv_desde_contenido.side_effect = CSVImportError({
                    'error': 'CSV inválido',
                    'codigo': 'CSV_VACIO'
                })

                resultado = procesar_mensaje(app_worker, payload)

            assert resultado is False
            db.session.refresh(job)
            assert job.estado == 'FALLIDO'
            assert 'CSV inválido' in job.mensaje_error
