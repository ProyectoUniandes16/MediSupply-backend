from src.services.pedidos import validate_order_against_products


def test_validate_no_products_returns_valid():
    res = validate_order_against_products([{'id': 1, 'cantidad': 1}], {})
    assert res['valid'] is True


def test_validate_missing_product_error():
    products = {'data': [{'id': 1, 'cantidad_disponible': 5}]}
    res = validate_order_against_products([{'id': 2, 'cantidad': 1}], products)
    assert res['valid'] is False
    assert res['errors'][0]['id'] == 2


def test_validate_quantity_exceeded():
    products = {'data': [{'id': 1, 'cantidad_disponible': 1}]}
    res = validate_order_against_products([{'id': 1, 'cantidad': 2}], products)
    assert res['valid'] is False
    assert 'Solicitado' in res['errors'][0]['msg']


def test_validate_total_inventario_field():
    products = {'data': [{'id': 1, 'totalInventario': 3}]}
    res = validate_order_against_products([{'id': 1, 'cantidad': 2}], products)
    assert res['valid'] is True
    assert res['available'][1] == 3


def test_validate_duplicates_sum():
    products = {'data': [{'id': 1, 'cantidad_disponible': 5}]}
    res = validate_order_against_products([{'id': 1, 'cantidad': 2}, {'id': 1, 'cantidad': 1}], products)
    assert res['valid'] is True
    assert res['requested'][1] == 3
