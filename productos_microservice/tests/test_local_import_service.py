import io
import os

from app.services.local_import_service import LocalImportService


class _DummyFileStorage:
    def __init__(self, data: bytes, filename: str):
        self.stream = io.BytesIO(data)
        self.filename = filename


def test_guardar_csv_with_stream(monkeypatch, tmp_path):
    monkeypatch.setattr(LocalImportService, "BASE_DIR", tmp_path.as_posix())
    dummy = _DummyFileStorage(b"col1,col2\n1,2\n", "datos prueba.csv")

    local_path, nombre_archivo = LocalImportService.guardar_csv(dummy, "tester")

    assert nombre_archivo == "datos prueba.csv"
    assert local_path.startswith(tmp_path.as_posix())
    assert os.path.exists(local_path)

    contenido = LocalImportService.leer_csv(local_path)
    assert "col1,col2" in contenido


def test_guardar_csv_with_file_like(monkeypatch, tmp_path):
    monkeypatch.setattr(LocalImportService, "BASE_DIR", tmp_path.as_posix())
    file_like = io.BytesIO(b"a,b,c\n1,2,3\n")
    file_like.name = "simple.csv"

    local_path, nombre_archivo = LocalImportService.guardar_csv(file_like, "tester")

    assert nombre_archivo == "simple.csv"
    assert os.path.exists(local_path)
    assert LocalImportService.leer_csv(local_path).startswith("a,b,c")
