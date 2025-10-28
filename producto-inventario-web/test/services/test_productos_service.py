import io
from types import SimpleNamespace
import pytest
import requests
from flask import Flask

from src.services.productos import (
    config,
    ProductoServiceError,
    crear_producto_externo,
    procesar_producto_batch,
    procesar_y_enviar_producto_batch,
    enviar_batch_productos,
    consultar_productos_externo,
    obtener_detalle_producto_externo,
    obtener_producto_por_sku_externo,
    descargar_certificacion_producto_externo,
)


class DummyFile:
    def __init__(self, name='cert.pdf', content=b'pdf'):
        self.filename = name
        self.stream = io.BytesIO(content)
        self.mimetype = 'application/pdf'


def make_csv(text):
    class File:
        def __init__(self, data):
            self.filename = 'test.csv'
            self.stream = io.BytesIO(data.encode('utf-8'))
            self.mimetype = 'text/csv'
    return File(text)


def make_response(status, json_data=None, text='', headers=None, raise_exc=None, content=b'binary-data'):
    headers = headers or {}
    def json_func():
        if isinstance(json_data, Exception):
            raise json_data
        return json_data
    def raise_for_status():
        if raise_exc:
            raise raise_exc
    return SimpleNamespace(status_code=status, json=json_func, text=text, headers=headers, raise_for_status=raise_for_status, content=content)


@pytest.fixture(autouse=True)
def _producto_url(mocker):
    mocker.patch.object(config, 'PRODUCTO_URL', 'http://productos')


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


def test_producto_service_creacion_y_batch(app, mocker):
    post_mock = mocker.patch('src.services.productos.requests.post')

    success_resp = make_response(201, {'id': 1})
    conflict_resp = make_response(400, {'error': 'bad', 'codigo': 'ERR'})
    raw_error_resp = make_response(500, json_data=Exception('invalid json'), text='Internal')

    with app.app_context():
        datos = {
            'nombre': 'Prod',
            'codigo_sku': 'SKU1',
            'categoria': 'Medicamentos',
            'precio_unitario': '10',
            'condiciones_almacenamiento': 'Seco',
            'fecha_vencimiento': '2026-01-01',
            'proveedor_id': '5'
        }

        with pytest.raises(ProductoServiceError) as exc:
            crear_producto_externo({}, {'certificacion': DummyFile()}, 'user')
        assert exc.value.status_code == 400

        with pytest.raises(ProductoServiceError) as exc:
            crear_producto_externo(datos, {}, 'user')
        assert exc.value.status_code == 400

        post_mock.side_effect = [success_resp]
        result = crear_producto_externo(datos, {'certificacion': DummyFile()}, 'user')
        assert result['id'] == 1

        post_mock.side_effect = [conflict_resp]
        with pytest.raises(ProductoServiceError) as exc:
            crear_producto_externo(datos, {'certificacion': DummyFile()}, 'user')
        assert exc.value.message['codigo'] == 'ERR'

        post_mock.side_effect = [raw_error_resp]
        with pytest.raises(ProductoServiceError) as exc:
            crear_producto_externo(datos, {'certificacion': DummyFile()}, 'user')
        assert exc.value.status_code == 500

        post_mock.side_effect = [requests.exceptions.RequestException('down')]
        with pytest.raises(requests.exceptions.RequestException):
            crear_producto_externo(datos, {'certificacion': DummyFile()}, 'user')

        valid_csv = make_csv("nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id\nA,SKU1,cat,10,Seco,2026-01-01,1")
        resumen = procesar_producto_batch(valid_csv, 'user')
        assert resumen['successful'] == 1

        invalid_csv = make_csv("nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id\n,,cat,abc,Seco,wrong,1")
        resumen_invalid = procesar_producto_batch(invalid_csv, 'user')
        assert resumen_invalid['failed'] == 1

        empty_csv = make_csv("nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id\n,,cat,abc,Seco,wrong,1")
        resultado = procesar_y_enviar_producto_batch(empty_csv, 'user')
        assert resultado['ok'] is False
        assert resultado['status'] == 400

        mocker.patch('src.services.productos.enviar_batch_productos', return_value={'sent': 1})
        valid_csv = make_csv("nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id\nB,SKU2,cat,12,Seco,2026-01-01,1")
        resultado = procesar_y_enviar_producto_batch(valid_csv, 'user')
        assert resultado['ok'] is True

        def raise_envio(*_):
            raise ProductoServiceError({'error': 'envio'}, 502)
        mocker.patch('src.services.productos.enviar_batch_productos', side_effect=raise_envio)
        valid_csv = make_csv("nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id\nC,SKU3,cat,15,Seco,2026-01-01,1")
        resultado = procesar_y_enviar_producto_batch(valid_csv, 'user')
        assert resultado['ok'] is False

        envio_ok = make_response(200, {'ok': True})
        envio_fail = make_response(400, {'error': 'bad', 'detail': 'x'})

        post_mock.side_effect = [envio_ok]
        res_envio = enviar_batch_productos(DummyFile('archivo.csv', b'csv'), 'user')
        assert res_envio['ok'] is True

        post_mock.side_effect = [envio_fail]
        with pytest.raises(ProductoServiceError) as exc:
            enviar_batch_productos(DummyFile('archivo.csv', b'csv'), 'user')
        assert exc.value.status_code == 400

        post_mock.side_effect = [requests.exceptions.RequestException('fail')]
        with pytest.raises(ProductoServiceError):
            enviar_batch_productos(DummyFile('archivo.csv', b'csv'), 'user')


def test_producto_service_consultas_y_descargas(app, mocker):
    mock_get = mocker.patch('src.services.productos.requests.get')

    with app.app_context():
        mock_get.side_effect = [make_response(200, {'items': [1], 'total': 1})]
        data = consultar_productos_externo({'q': 'x'})
        assert data['total'] == 1

        mock_get.side_effect = [make_response(400, {'error': 'bad', 'codigo': 'ERR'})]
        with pytest.raises(ProductoServiceError) as exc:
            consultar_productos_externo()
        assert exc.value.status_code == 400

        mock_get.side_effect = [requests.exceptions.RequestException('network')]
        with pytest.raises(ProductoServiceError) as exc:
            consultar_productos_externo()
        assert exc.value.status_code == 503

        mock_get.side_effect = [make_response(200, {'id': 5}), make_response(404, {}), make_response(500, {'error': 'interno'}), requests.exceptions.RequestException('down')]
        detalle = obtener_detalle_producto_externo(5)
        assert detalle['id'] == 5

        with pytest.raises(ProductoServiceError) as exc:
            obtener_detalle_producto_externo(5)
        assert exc.value.status_code == 404

        with pytest.raises(ProductoServiceError) as exc:
            obtener_detalle_producto_externo(5)
        assert exc.value.status_code == 500

        with pytest.raises(ProductoServiceError) as exc:
            obtener_detalle_producto_externo(5)
        assert exc.value.status_code == 503

        with pytest.raises(ProductoServiceError) as exc:
            obtener_producto_por_sku_externo('')
        assert exc.value.status_code == 400

        mock_get.side_effect = [make_response(200, {'id': 3}), make_response(404, {})]
        producto = obtener_producto_por_sku_externo('SKU-1')
        assert producto['id'] == 3

        with pytest.raises(ProductoServiceError) as exc:
            obtener_producto_por_sku_externo('SKU-1')
        assert exc.value.status_code == 404

        mock_get.side_effect = [
            make_response(200, text='', headers={'Content-Type': 'application/pdf', 'Content-Disposition': 'attachment; filename="cert.pdf"'}, json_data={'unused': True}, content=b'%PDF-1.4'),
            make_response(404, {}),
            make_response(500, {'error': 'fail'}, text='fail'),
            requests.exceptions.RequestException('net')
        ]
        content, filename, mimetype = descargar_certificacion_producto_externo(2)
        assert filename == 'cert.pdf'
        assert mimetype == 'application/pdf'
        assert content.startswith(b'%PDF')

        with pytest.raises(ProductoServiceError) as exc:
            descargar_certificacion_producto_externo(2)
        assert exc.value.status_code == 404

        with pytest.raises(ProductoServiceError) as exc:
            descargar_certificacion_producto_externo(2)
        assert exc.value.status_code == 500

        with pytest.raises(ProductoServiceError) as exc:
            descargar_certificacion_producto_externo(2)
        assert exc.value.status_code == 503
