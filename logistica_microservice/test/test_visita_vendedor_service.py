import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.services.visita_vendedor_service import (
    crear_visita_vendedor,
    VisitaVendedorServiceError,
)
from src.models.visita_vendedor import VisitaVendedor


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

    visita = captured["instance"]
    assert visita.cliente_id == 10
    assert visita.vendedor_id == "v-10"
    assert visita.nombre_contacto is None
    assert visita.latitud is None
    assert visita.fecha_fin_visita is None


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
            "nombre_contacto": "   Ana Perez   ",
            "latitud": "4.6123456",
            "longitud": "-74.0723456",
            "fecha_fin_visita": "2025-10-12 15:30:00",
            "comentarios": "  Buen cliente  ",
        }

        resultado = crear_visita_vendedor(payload)

    assert resultado["estado"] == "en progreso"
    assert resultado["nombre_contacto"] == "Ana Perez"
    assert resultado["latitud"] == pytest.approx(4.6123456, rel=1e-9)
    assert resultado["longitud"] == pytest.approx(-74.0723456, rel=1e-9)
    assert resultado["fecha_fin_visita"].startswith("2025-10-12")
    assert resultado["comentarios"] == "Buen cliente"

    visita = captured["instance"]
    assert visita.fecha_fin_visita == datetime(2025, 10, 12, 15, 30)
    assert float(visita.latitud) == pytest.approx(4.6123456, rel=1e-9)
    assert float(visita.longitud) == pytest.approx(-74.0723456, rel=1e-9)


def test_crear_visita_vendedor_geolocalizacion_incompleta(app):
    with app.app_context():
        payload = {
            "cliente_id": 12,
            "vendedor_id": "v-12",
            "fecha_visita": "2025-10-12",
            "latitud": 4.1,
        }

        with pytest.raises(VisitaVendedorServiceError) as exc:
            crear_visita_vendedor(payload)

        assert exc.value.status_code == 400
        assert exc.value.message.get("codigo") == "GEO_INCOMPLETA"


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