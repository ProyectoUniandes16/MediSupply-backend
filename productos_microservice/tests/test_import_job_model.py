from datetime import datetime, timedelta

from app.extensions import db
from app.models.import_job import ImportJob


def _crear_job_basico():
    return ImportJob(
        id="job-test-1",
        nombre_archivo="productos.csv",
        usuario_registro="tester@example.com"
    )


def test_to_dict_includes_core_fields(app):
    with app.app_context():
        job = _crear_job_basico()
        job.total_filas = 20
        job.actualizar_progreso(filas_procesadas=5, exitosos=4, fallidos=1)
        job.fecha_inicio_proceso = datetime.utcnow() - timedelta(seconds=10)
        job.fecha_finalizacion = datetime.utcnow()

        db.session.add(job)
        db.session.commit()

        data = job.to_dict()

        assert data["job_id"] == job.id
        assert data["nombre_archivo"] == "productos.csv"
        assert data["progreso"] == round(job.progreso, 2)
        assert data["tiempo_transcurrido_segundos"] >= 10
        assert data["exitosos"] == 4
        assert "detalles_errores" not in data


def test_to_dict_limits_error_details(app):
    with app.app_context():
        job = _crear_job_basico()
        job.detalles_errores = [{"fila": i, "error": "Error"} for i in range(15)]
        job.mensaje_error = "Fallo de importación"

        db.session.add(job)
        db.session.commit()

        data = job.to_dict(include_errors=True)

        assert data["mensaje_error"] == "Fallo de importación"
        assert len(data["detalles_errores"]) == 10
        assert data["total_errores"] == 15
        assert "nota" in data

        data_without_errors = job.to_dict(include_errors=False)
        assert "detalles_errores" not in data_without_errors


def test_estado_helpers_and_progress_updates(app):
    with app.app_context():
        job = _crear_job_basico()
        job.total_filas = 8

        db.session.add(job)
        db.session.commit()

        job.marcar_como_procesando()
        assert job.estado == "PROCESANDO"
        assert job.fecha_inicio_proceso is not None

        job.actualizar_progreso(filas_procesadas=4, exitosos=3, fallidos=1)
        assert job.progreso == 50.0
        assert job.exitosos == 3
        assert job.fallidos == 1

        job.marcar_como_completado("Importación finalizada")
        assert job.estado == "COMPLETADO"
        assert job.progreso == 100.0
        assert job.extra_metadata["mensaje_finalizacion"] == "Importación finalizada"
        assert job.es_terminal() is True

        job.marcar_como_fallido("Error crítico")
        assert job.estado == "FALLIDO"
        assert job.es_terminal() is True
        assert job.puede_reintentar() is True

        job.reintentos = 2
        assert job.puede_reintentar(max_reintentos=2) is False
