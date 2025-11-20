import importlib

import pytest

from app.config import minio_config as minio_config_module


def _reload_config(monkeypatch, **env_vars):
    keys = {
        'MINIO_ENDPOINT',
        'MINIO_ACCESS_KEY',
        'MINIO_SECRET_KEY',
        'MINIO_SECURE',
        'MINIO_BUCKET_VIDEOS',
        'PRESIGNED_URL_EXPIRY',
        'USE_MINIO'
    }
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    importlib.reload(minio_config_module)
    return minio_config_module.MinIOConfig


def test_minio_config_disabled(monkeypatch):
    config_cls = _reload_config(monkeypatch, USE_MINIO='false')
    estado = config_cls.verificar_configuracion()
    assert estado['minio_configurado'] is False
    assert 'MinIO deshabilitado' in estado['errores'][0]


def test_minio_config_missing_credentials(monkeypatch):
    config_cls = _reload_config(
        monkeypatch,
        USE_MINIO='true',
        MINIO_ENDPOINT='',
        MINIO_ACCESS_KEY='',
        MINIO_SECRET_KEY=''  # deliberately empty
    )
    estado = config_cls.verificar_configuracion()
    assert estado['minio_configurado'] is False
    assert any('MINIO_ENDPOINT' in error or 'Credenciales' in error for error in estado['errores'])


def test_minio_config_valida(monkeypatch):
    config_cls = _reload_config(
        monkeypatch,
        USE_MINIO='true',
        MINIO_ENDPOINT='minio:9000',
        MINIO_ACCESS_KEY='access',
        MINIO_SECRET_KEY='secret',
        PRESIGNED_URL_EXPIRY='7200'
    )
    estado = config_cls.verificar_configuracion()
    assert estado['minio_configurado'] is True
    assert estado['errores'] == []
