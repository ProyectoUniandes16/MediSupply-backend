import logging
import pytest

from flask import Flask

from src import create_app


def test_create_app_returns_flask_app():
    app = create_app()
    assert isinstance(app, Flask)
    # Blueprints registered
    assert 'auth' in app.blueprints
    assert 'health' in app.blueprints


def test_create_app_handles_db_create_all_exception(monkeypatch, caplog):
    # Forzar que db.create_all lance una excepción
    import src.models.user as user_mod

    def fake_create_all():
        raise RuntimeError('DB not available')

    monkeypatch.setattr(user_mod.db, 'create_all', fake_create_all)

    caplog.set_level(logging.WARNING)
    app = create_app()
    # La app debería haberse creado y haberse registrado el warning
    found = any('No se pudieron crear las tablas de la base de datos' in r.message for r in caplog.records)
    assert found
