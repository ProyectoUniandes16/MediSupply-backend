import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.services.visita_vendedor_service import (
    crear_visita_vendedor,
    actualizar_visita_vendedor,
    listar_visitas_vendedor,
    VisitaVendedorServiceError,
)
from src.models.visita_vendedor import VisitaVendedor
from src.models.zona import db


def test_crear_visita_vendedor_minimo(app, monkeypatch):
    captured = {}

    def fake_save(self):
        captured["instance"] = self
        # Simula asignación de PK como lo haría la BD
        self.id = 1
        return self

    monkeypatch.setattr(VisitaVendedor, "save", fake_save)

    with app.app_context():
        payload = {
            "cliente_id": 10,
            "vendedor_id": "v-10",
            "fecha_visita": "2025-10-12",
        }

        resultado = crear_visita_vendedor(payload)

    assert resultado["estado"] == "pendiente"
    assert resultado["cliente_id"] == 10
    assert resultado["vendedor_id"] == "v-10"
    assert resultado["comentarios"] is None

    visita = captured["instance"]
    assert visita.cliente_id == 10
    assert visita.vendedor_id == "v-10"


def test_crear_visita_vendedor_con_opcionales(app, monkeypatch):
    captured = {}

    def fake_save(self):
        captured["instance"] = self
        self.id = 22
        return self

    monkeypatch.setattr(VisitaVendedor, "save", fake_save)

    with app.app_context():
        payload = {
            "cliente_id": 11,
            "vendedor_id": "v-11",
            "fecha_visita": "12/10/2025",
            "estado": "en progreso",
            "comentarios": "  Buen cliente  ",
        }

        resultado = crear_visita_vendedor(payload)

    assert resultado["estado"] == "en progreso"
    assert resultado["comentarios"] == "Buen cliente"
    assert "nombre_contacto" not in resultado
    assert "latitud" not in resultado
    assert "longitud" not in resultado
    assert "fecha_fin_visita" not in resultado

    visita = captured["instance"]
    assert visita.estado == "en progreso"
    assert visita.comentarios == "Buen cliente"


def test_crear_visita_vendedor_comentarios_normalizados(app, monkeypatch):
    captured = {}

    def fake_save(self):
        captured["instance"] = self
        self.id = 45
        return self

    monkeypatch.setattr(VisitaVendedor, "save", fake_save)

    with app.app_context():
        payload = {
            "cliente_id": 15,
            "vendedor_id": "v-15",
            "fecha_visita": "2025-10-12",
            "comentarios": "  Observación directa  ",
        }

        resultado = crear_visita_vendedor(payload)

    assert resultado["comentarios"] == "Observación directa"

    visita = captured["instance"]
    assert visita.comentarios == "Observación directa"
def test_crear_visita_vendedor_estado_invalido(app):
    with app.app_context():
        payload = {
            "cliente_id": 13,
            "vendedor_id": "v-13",
            "fecha_visita": "2025-10-12",
            "estado": "cancelado",
        }

        with pytest.raises(VisitaVendedorServiceError) as exc:
            crear_visita_vendedor(payload)

        assert exc.value.status_code == 400
        assert exc.value.message.get("codigo") == "ESTADO_INVALIDO"


def test_crear_visita_vendedor_duplicada(app, monkeypatch):
    call_count = {"count": 0}

    def fake_save(self):
        call_count["count"] += 1
        if call_count["count"] == 1:
            self.id = 33
            return self
        raise IntegrityError("stmt", {}, Exception("duplicate"))

    monkeypatch.setattr(VisitaVendedor, "save", fake_save)

    with app.app_context():
        payload = {
            "cliente_id": 14,
            "vendedor_id": "v-14",
            "fecha_visita": "2025-10-12",
        }

        crear_visita_vendedor(payload)

        with pytest.raises(VisitaVendedorServiceError) as exc:
            crear_visita_vendedor(payload)

    assert call_count["count"] == 2
    assert exc.value.status_code == 409
    assert exc.value.message.get("codigo") == "VISITA_DUPLICADA"


def test_actualizar_visita_vendedor_estado_y_observacion(app):
    with app.app_context():
        visita = VisitaVendedor(
            cliente_id=21,
            vendedor_id="v-21",
            fecha_visita=datetime(2025, 10, 12).date(),
            estado="pendiente",
        )
        db.session.add(visita)
        db.session.commit()

        payload = {"estado": "finalizado", "comentarios": "Visita completada"}
        resultado = actualizar_visita_vendedor(visita.id, payload)

        assert resultado["estado"] == "finalizado"
        assert resultado["comentarios"] == "Visita completada"

        refrescada = db.session.get(VisitaVendedor, visita.id)
        assert refrescada.estado == "finalizado"
        assert refrescada.comentarios == "Visita completada"


def test_actualizar_visita_vendedor_observacion_vacia(app):
    with app.app_context():
        visita = VisitaVendedor(
            cliente_id=22,
            vendedor_id="v-22",
            fecha_visita=datetime(2025, 10, 12).date(),
            estado="en progreso",
            comentarios="Anterior",
        )
        db.session.add(visita)
        db.session.commit()

        resultado = actualizar_visita_vendedor(
            visita.id,
            {"estado": "pendiente", "comentarios": "   "},
        )

        assert resultado["estado"] == "pendiente"
        assert resultado["comentarios"] is None

        refrescada = db.session.get(VisitaVendedor, visita.id)
        assert refrescada.comentarios is None


def test_actualizar_visita_vendedor_estado_invalido(app):
    with app.app_context():
        visita = VisitaVendedor(
            cliente_id=23,
            vendedor_id="v-23",
            fecha_visita=datetime(2025, 10, 12).date(),
            estado="pendiente",
        )
        db.session.add(visita)
        db.session.commit()

        with pytest.raises(VisitaVendedorServiceError) as exc:
            actualizar_visita_vendedor(visita.id, {"estado": "cancelado"})

        assert exc.value.status_code == 400
        assert exc.value.message.get("codigo") == "ESTADO_INVALIDO"


def test_actualizar_visita_vendedor_no_encontrada(app):
    with app.app_context():
        with pytest.raises(VisitaVendedorServiceError) as exc:
            actualizar_visita_vendedor(9999, {"estado": "pendiente"})

        assert exc.value.status_code == 404
        assert exc.value.message.get("codigo") == "VISITA_NO_ENCONTRADA"


def test_actualizar_visita_vendedor_estado_faltante(app):
    with app.app_context():
        visita = VisitaVendedor(
            cliente_id=24,
            vendedor_id="v-24",
            fecha_visita=datetime(2025, 10, 12).date(),
            estado="pendiente",
        )
        db.session.add(visita)
        db.session.commit()

        with pytest.raises(VisitaVendedorServiceError) as exc:
            actualizar_visita_vendedor(visita.id, {"comentarios": "sin estado"})

        assert exc.value.status_code == 400
        assert exc.value.message.get("codigo") == "ESTADO_REQUERIDO"


def test_listar_visitas_vendedor_sin_rango(app):
    with app.app_context():
        visita_1 = VisitaVendedor(
            cliente_id=1,
            vendedor_id="v-30",
            fecha_visita=datetime(2025, 11, 10).date(),
            estado="pendiente",
        )
        visita_2 = VisitaVendedor(
            cliente_id=2,
            vendedor_id="v-30",
            fecha_visita=datetime(2025, 11, 12).date(),
            estado="en progreso",
        )
        db.session.add_all([visita_1, visita_2])
        db.session.commit()

        resultado = listar_visitas_vendedor("v-30")

        assert len(resultado) == 2
        assert resultado[0]["id_visita"] == visita_1.id
        assert resultado[1]["estado"] == "en progreso"


def test_listar_visitas_vendedor_con_rango(app):
    with app.app_context():
        visitas = [
            VisitaVendedor(
                cliente_id=1,
                vendedor_id="v-31",
                fecha_visita=datetime(2025, 11, 10).date(),
                estado="pendiente",
            ),
            VisitaVendedor(
                cliente_id=2,
                vendedor_id="v-31",
                fecha_visita=datetime(2025, 11, 12).date(),
                estado="en progreso",
            ),
            VisitaVendedor(
                cliente_id=3,
                vendedor_id="v-31",
                fecha_visita=datetime(2025, 11, 20).date(),
                estado="finalizado",
            ),
        ]
        db.session.add_all(visitas)
        db.session.commit()

        resultado = listar_visitas_vendedor(
            "v-31",
            fecha_inicio="2025-11-11",
            fecha_fin="2025-11-20",
        )

        assert len(resultado) == 2
        assert all(item["fecha_visita"] >= "2025-11-11" for item in resultado)
        assert resultado[-1]["estado"] == "finalizado"


def test_listar_visitas_vendedor_rango_incompleto(app):
    with app.app_context():
        with pytest.raises(VisitaVendedorServiceError) as exc:
            listar_visitas_vendedor("v-32", fecha_inicio="2025-11-11")

        assert exc.value.status_code == 400
        assert exc.value.message.get("codigo") == "RANGO_FECHAS_INCOMPLETO"


def test_listar_visitas_vendedor_sin_vendedor_id(app):
    with app.app_context():
        with pytest.raises(VisitaVendedorServiceError) as exc:
            listar_visitas_vendedor(None)

        assert exc.value.status_code == 400
        assert exc.value.message.get("codigo") == "VENDEDOR_ID_REQUERIDO"