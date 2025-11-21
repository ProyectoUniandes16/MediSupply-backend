from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import patch

from app.extensions import db
from app.models.import_job import ImportJob
from app.models.producto import Producto, CertificacionProducto


def _crear_producto(app, tmp_path, nombre="Producto Demo", sku="SKU-DEMO-1", categoria="medicamento"):
    with app.app_context():
        producto = Producto(
            nombre=nombre,
            codigo_sku=sku,
            categoria=categoria,
            precio_unitario=25.5,
            condiciones_almacenamiento="Ambiente controlado",
            fecha_vencimiento=datetime(2026, 12, 31).date(),
            proveedor_id=1,
            usuario_registro="tester@example.com",
            cantidad_disponible=10
        )
        db.session.add(producto)
        db.session.flush()
        producto_id = producto.id

        cert_path = tmp_path / f"cert_{sku}.pdf"
        cert_path.write_text("Contenido de certificacion")

        certificacion = CertificacionProducto(
            producto_id=producto_id,
            tipo_certificacion="INVIMA",
            nombre_archivo="cert.pdf",
            ruta_archivo=str(cert_path),
            tamaño_archivo=cert_path.stat().st_size,
            fecha_vencimiento_cert=datetime(2027, 12, 31).date()
        )
        db.session.add(certificacion)
        db.session.commit()

        return Producto.query.get(producto_id)


def test_listar_productos_con_filtros(client, app, tmp_path):
    producto = _crear_producto(app, tmp_path, nombre="Ibuprofeno", sku="SKU-IBU-1")

    response = client.get(
        "/api/productos/",
        query_string={
            "page": 1,
            "per_page": 5,
            "categoria": producto.categoria,
            "estado": "Activo",
            "buscar": "Ibu",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["productos"][0]["codigo_sku"] == "SKU-IBU-1"
    assert data["productos"][0]["tiene_certificacion"] is True
    assert data["paginacion"]["pagina_actual"] == 1


@patch("app.services.producto_service.ProductoService.obtener_detalle_completo")
def test_obtener_producto_por_id(mock_detalle, client):
    mock_detalle.return_value = {"id": 1, "nombre": "Demo"}
    response = client.get("/api/productos/1")
    assert response.status_code == 200
    assert response.get_json()["producto"]["nombre"] == "Demo"


def test_obtener_producto_por_id_no_encontrado(client):
    response = client.get("/api/productos/12345")
    assert response.status_code == 404
    body = response.get_json()
    assert body["codigo"] == "PRODUCTO_NO_ENCONTRADO"


@patch("app.services.producto_service.ProductoService.obtener_detalle_completo")
def test_obtener_producto_por_sku(mock_detalle, client):
    mock_detalle.return_value = {"codigo_sku": "SKU-DEMO"}
    response = client.get("/api/productos/sku/SKU-DEMO")
    assert response.status_code == 200
    assert response.get_json()["producto"]["codigo_sku"] == "SKU-DEMO"


def test_descargar_certificacion_sin_certificacion(client, app):
    with app.app_context():
        producto = Producto(
            nombre="Sin Cert",
            codigo_sku="SKU-NO-CERT",
            categoria="medicamento",
            precio_unitario=10,
            condiciones_almacenamiento="Seco",
            fecha_vencimiento=datetime.utcnow().date(),
            proveedor_id=1,
            usuario_registro="tester@example.com",
        )
        db.session.add(producto)
        db.session.commit()
        producto_id = producto.id

    response = client.get(f"/api/productos/{producto_id}/certificacion/descargar")
    assert response.status_code == 404
    assert response.get_json()["codigo"] == "CERTIFICACION_NO_ENCONTRADA"


def test_descargar_certificacion_producto_no_existe(client):
    response = client.get("/api/productos/9999/certificacion/descargar")
    assert response.status_code == 404
    assert response.get_json()["codigo"] == "PRODUCTO_NO_ENCONTRADO"


@patch("app.services.csv_service.CSVProductoService.importar_productos_csv")
def test_importar_csv_sincrono(mock_importar, client):
    mock_importar.return_value = {
        "total_filas": 1,
        "exitosos": 1,
        "fallidos": 0,
        "detalles_exitosos": [{"sku": "SKU-1"}],
        "detalles_errores": [],
    }

    contenido = "sku,nombre\nSKU-1,Producto 1\n".encode("utf-8")
    data = {
        "usuario_registro": "tester@example.com",
        "archivo": (BytesIO(contenido), "import.csv"),
    }

    response = client.post(
        "/api/productos/importar-csv",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["procesamiento"] == "sincrono"
    assert body["resumen"]["exitosos"] == 1


@patch("app.services.redis_import_queue_service.RedisImportQueueService.publicar_import_job", return_value=True)
@patch("app.services.local_import_service.LocalImportService.guardar_csv")
def test_importar_csv_asincrono(mock_guardar, mock_publicar, client, tmp_path):
    local_file = tmp_path / "bulk.csv"
    local_file.write_text("contenido")
    mock_guardar.return_value = (str(local_file), "bulk.csv")

    filas = "\n".join([f"SKU-{i},Producto {i}" for i in range(101)])
    contenido = f"sku,nombre\n{filas}\n".encode("utf-8")
    data = {
        "usuario_registro": "tester@example.com",
        "archivo": (BytesIO(contenido), "bulk.csv"),
        "forzar_asincrono": "true",
    }

    response = client.post(
        "/api/productos/importar-csv",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 202
    body = response.get_json()
    assert body["procesamiento"] == "asincrono"
    assert "job_id" in body


@patch("app.services.redis_import_queue_service.RedisImportQueueService.publicar_import_job", return_value=False)
@patch("app.services.local_import_service.LocalImportService.guardar_csv")
def test_importar_csv_asincrono_error_redis(mock_guardar, mock_publicar, client, tmp_path):
    local_file = tmp_path / "bulk_error.csv"
    local_file.write_text("contenido")
    mock_guardar.return_value = (str(local_file), "bulk_error.csv")

    filas = "\n".join([f"SKU-{i},Producto {i}" for i in range(120)])
    contenido = f"sku,nombre\n{filas}\n".encode("utf-8")
    data = {
        "usuario_registro": "tester@example.com",
        "archivo": (BytesIO(contenido), "bulk_error.csv"),
    }

    response = client.post(
        "/api/productos/importar-csv",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["codigo"] == "ERROR_REDIS_QUEUE"


def test_obtener_status_importacion(client, app):
    with app.app_context():
        job = ImportJob(
            id="job-status-1",
            nombre_archivo="bulk.csv",
            local_path="/tmp/bulk.csv",
            estado="COMPLETADO",
            total_filas=5,
            exitosos=4,
            fallidos=1,
            usuario_registro="tester@example.com",
            fecha_inicio_proceso=datetime.utcnow() - timedelta(minutes=1),
            fecha_finalizacion=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()

    response = client.get("/api/productos/importar-csv/status/job-status-1")
    assert response.status_code == 200
    body = response.get_json()
    assert body["mensaje"].startswith("Importación completada")
    assert body["validaciones"]["productos_con_errores"] == 1


def test_obtener_status_importacion_no_encontrado(client):
    response = client.get("/api/productos/importar-csv/status/no-existe")
    assert response.status_code == 404
    assert response.get_json()["codigo"] == "JOB_NO_ENCONTRADO"


def test_listar_jobs_importacion_con_filtros(client, app):
    with app.app_context():
        jobs = [
            ImportJob(
                id=f"job-{i}",
                nombre_archivo=f"archivo_{i}.csv",
                local_path=f"/tmp/archivo_{i}.csv",
                estado="EN_COLA" if i % 2 == 0 else "COMPLETADO",
                usuario_registro="tester@example.com" if i < 2 else "otro@example.com",
            )
            for i in range(4)
        ]
        db.session.add_all(jobs)
        db.session.commit()

    response = client.get(
        "/api/productos/importar-csv/jobs",
        query_string={"usuario": "tester@example.com", "estado": "EN_COLA", "limit": 2},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["paginacion"]["limit"] == 2
    assert all(job["usuario_registro"] == "tester@example.com" for job in body["jobs"])
    assert all(job["estado"] == "EN_COLA" for job in body["jobs"])