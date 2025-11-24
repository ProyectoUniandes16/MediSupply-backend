import pytest

from src.services.pedidos import PedidoServiceError
import src.blueprints.pedidos as pedidos_bp_module


def test_crear_pedido_success(client):
    data = {
        'cliente_id': 99,
        'total': 5.0,
        'productos': [{'id': 1, 'cantidad': 1, 'precio': 5.0}]
    }

    response = client.post('/pedido', json=data)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['cliente_id'] == 99


def test_crear_pedido_service_error(client, monkeypatch):
    # monkeypatch the registrar_pedido used by the blueprint to raise a service error
    def raise_service_error(data):
        raise PedidoServiceError({'error': 'bad'}, 400)

    monkeypatch.setattr(pedidos_bp_module, 'registrar_pedido', raise_service_error)

    response = client.post('/pedido', json={'cliente_id': 1})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'bad'}


def test_crear_pedido_unexpected_exception(client, monkeypatch):
    # monkeypatch to raise a generic exception and expect 500
    def raise_exc(data):
        # use a specific exception type for clarity
        raise RuntimeError('boom')

    monkeypatch.setattr(pedidos_bp_module, 'registrar_pedido', raise_exc)

    response = client.post('/pedido', json={'cliente_id': 1})
    assert response.status_code == 500
    body = response.get_json()
    assert body.get('codigo') == 'ERROR_INTERNO_SERVIDOR'


def test_obtener_pedidos_without_filters(client, session):
    # seed pedidos directly in DB
    from src.models.pedios import Pedido

    p1 = Pedido(cliente_id=11, estado='pendiente', total=1.0, vendedor_id='vA')
    p2 = Pedido(cliente_id=12, estado='pendiente', total=2.0, vendedor_id='vB')
    session.add(p1)
    session.add(p2)
    session.commit()

    response = client.get('/pedido')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data['data'], list)
    assert len(data['data']) >= 2


def test_obtener_pedidos_filtering(client, session):
    from src.models.pedios import Pedido

    p = Pedido(cliente_id=55, estado='pendiente', total=3.0, vendedor_id='X123')
    session.add(p)
    p2 = Pedido(cliente_id=55, estado='entregado', total=4.0, vendedor_id='X123')
    session.add(p2)
    session.commit()

    # filter by vendedor
    response = client.get('/pedido?vendedor_id=X123')
    assert response.status_code == 200
    data = response.get_json()['data']
    assert all(item.get('vendedor_id') == 'X123' for item in data)

    # filter by cliente
    response = client.get('/pedido?cliente_id=55')
    assert response.status_code == 200
    data = response.get_json()['data']
    assert all(item.get('cliente_id') == 55 for item in data)

    # filter by estado
    response = client.get('/pedido?estado=entregado')
    assert response.status_code == 200
    data = response.get_json()['data']
    assert all(item.get('estado') == 'entregado' for item in data)


def test_obtener_detalle_pedido_success(client, session):
    from src.models.pedios import Pedido
    from src.models.pedidos_productos import PedidoProducto

    # crear pedido y producto asociado
    p = Pedido(cliente_id=200, estado='pendiente', total=9.0, vendedor_id='V1')
    session.add(p)
    session.commit()

    pp = PedidoProducto(pedido_id=p.id, producto_id=10, cantidad=3, precio=2.5)
    session.add(pp)
    session.commit()

    resp = client.get(f'/pedido/{p.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['data']['id'] == p.id
    assert isinstance(data['data']['productos'], list)
    assert data['data']['productos'][0]['producto_id'] == 10
    assert data['data']['productos'][0]['cantidad'] == 3


def test_obtener_detalle_pedido_service_error(client, monkeypatch):
    # parchear la función detalle_pedido para lanzar un error controlado
    def raise_service(pedido_id):
        raise PedidoServiceError({'error': 'No encontrado'}, 404)

    monkeypatch.setattr(pedidos_bp_module, 'detalle_pedido', raise_service)
    resp = client.get('/pedido/999')
    assert resp.status_code == 404
    assert resp.get_json() == {'error': 'No encontrado'}


def test_actualizar_estado_pedido_success(client, session):
    from src.models.pedios import Pedido

    p = Pedido(cliente_id=1, estado='pendiente', total=10.0, vendedor_id='v1')
    session.add(p)
    session.commit()

    response = client.patch(f'/pedido/{p.id}/estado', json={'estado': 'en_proceso'})
    assert response.status_code == 200
    assert response.get_json() == {"message": "Estado actualizado"}

    # Verificar en DB
    session.refresh(p)
    assert p.estado == 'en_proceso'


def test_actualizar_estado_pedido_missing_estado(client, session):
    from src.models.pedios import Pedido

    p = Pedido(cliente_id=1, estado='pendiente', total=10.0, vendedor_id='v1')
    session.add(p)
    session.commit()

    response = client.patch(f'/pedido/{p.id}/estado', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Estado requerido', 'codigo': 'ESTADO_REQUERIDO'}


def test_actualizar_estado_pedido_not_found(client):
    response = client.patch('/pedido/99999/estado', json={'estado': 'en_proceso'})
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Pedido no encontrado', 'codigo': 'PEDIDO_NO_ENCONTRADO'}
