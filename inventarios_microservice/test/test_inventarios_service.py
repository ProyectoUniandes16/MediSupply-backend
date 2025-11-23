from types import SimpleNamespace
import pytest
from sqlalchemy.exc import IntegrityError

from app.services.inventarios_service import (
    crear_inventario,
    listar_inventarios,
    obtener_inventario_por_id,
    actualizar_inventario,
    eliminar_inventario,
    ajustar_cantidad,
    ValidationError,
    ConflictError,
    NotFoundError,
)


@pytest.fixture
def mock_db(mocker):
    """Provide a mocked db.session object for service calls."""
    session_mock = mocker.MagicMock()
    db_mock = mocker.MagicMock()
    db_mock.session = session_mock
    mocker.patch('app.services.inventarios_service.db', db_mock)
    return session_mock


@pytest.fixture
def mock_uuid(mocker):
    mocker.patch('app.services.inventarios_service.uuid4', return_value='test-uuid')


def _build_inventario_instance(mocker, **overrides):
    """Helper to create an inventario-like object for _to_dict."""
    defaults = {
        'id': 'test-uuid',
        'producto_id': 1,
        'cantidad': 10,
        'ubicacion': 'Almacen',
        'usuario_creacion': 'tester',
        'usuario_actualizacion': 'tester',
        'fecha_creacion': mocker.MagicMock(),
        'fecha_actualizacion': mocker.MagicMock(),
    }
    defaults.update(overrides)
    defaults['fecha_creacion'].isoformat.return_value = '2024-01-01T00:00:00'
    defaults['fecha_actualizacion'].isoformat.return_value = '2024-01-01T00:00:00'
    return SimpleNamespace(**defaults)


def _setup_inventario_model(mocker, query=None, instance=None):
    """Patch the Inventario model to control constructor and query attribute."""
    mock_model = mocker.MagicMock()
    if instance is None:
        instance = mocker.MagicMock()
    mock_model.return_value = instance
    if query is not None:
        mock_model.query = query
    mocker.patch('app.services.inventarios_service.Inventario', mock_model)
    return mock_model, instance


def test_crear_inventario_success(mocker, mock_db, mock_uuid, sample_inventario_data):
    filter_by_mock = mocker.MagicMock()
    filter_by_mock.first.return_value = None
    query_mock = mocker.MagicMock()
    query_mock.filter_by.return_value = filter_by_mock
    inventario_instance = _build_inventario_instance(
        mocker,
        producto_id=sample_inventario_data['productoId'],
        cantidad=sample_inventario_data['cantidad'],
        ubicacion=sample_inventario_data['ubicacion'],
        usuario_creacion=sample_inventario_data['usuario'],
        usuario_actualizacion=sample_inventario_data['usuario'],
    )
    _setup_inventario_model(mocker, query=query_mock, instance=inventario_instance)
    queue_spy = mocker.patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')

    result = crear_inventario(sample_inventario_data)

    assert result == {
        'id': 'test-uuid',
        'productoId': sample_inventario_data['productoId'],
        'cantidad': sample_inventario_data['cantidad'],
        'ubicacion': sample_inventario_data['ubicacion'],
        'usuarioCreacion': sample_inventario_data['usuario'],
        'fechaCreacion': '2024-01-01T00:00:00',
        'usuarioActualizacion': sample_inventario_data['usuario'],
        'fechaActualizacion': '2024-01-01T00:00:00',
    }
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    queue_spy.assert_called_once_with(
        producto_id=sample_inventario_data['productoId'],
        action='create',
        data=result,
    )


def test_crear_inventario_conflict_when_exists(mocker, mock_db, sample_inventario_data):
    filter_by_mock = mocker.MagicMock()
    filter_by_mock.first.return_value = object()
    query_mock = mocker.MagicMock()
    query_mock.filter_by.return_value = filter_by_mock
    _setup_inventario_model(mocker, query=query_mock)

    with pytest.raises(ConflictError):
        crear_inventario(sample_inventario_data)

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_crear_inventario_invalid_producto_id(sample_inventario_data):
    bad_payload = dict(sample_inventario_data, productoId='invalid')

    with pytest.raises(ValidationError):
        crear_inventario(bad_payload)


def test_crear_inventario_foreign_key_error(mocker, mock_db, sample_inventario_data):
    filter_by_mock = mocker.MagicMock()
    filter_by_mock.first.return_value = None
    query_mock = mocker.MagicMock()
    query_mock.filter_by.return_value = filter_by_mock
    inventario_instance = _build_inventario_instance(mocker)
    _setup_inventario_model(mocker, query=query_mock, instance=inventario_instance)
    mock_db.commit.side_effect = IntegrityError('stmt', 'params', Exception('foreign key constraint failed'))

    with pytest.raises(NotFoundError):
        crear_inventario(sample_inventario_data)

    mock_db.rollback.assert_called_once()


def test_crear_inventario_integrity_error_unique(mocker, mock_db, sample_inventario_data):
    filter_by_mock = mocker.MagicMock()
    filter_by_mock.first.return_value = None
    query_mock = mocker.MagicMock()
    query_mock.filter_by.return_value = filter_by_mock
    inventario_instance = _build_inventario_instance(mocker)
    _setup_inventario_model(mocker, query=query_mock, instance=inventario_instance)
    mock_db.commit.side_effect = IntegrityError('stmt', 'params', Exception('unique constraint failed'))

    with pytest.raises(ConflictError):
        crear_inventario(sample_inventario_data)

    mock_db.rollback.assert_called_once()


def test_crear_inventario_generic_exception(mocker, mock_db, sample_inventario_data):
    filter_by_mock = mocker.MagicMock()
    filter_by_mock.first.return_value = None
    query_mock = mocker.MagicMock()
    query_mock.filter_by.return_value = filter_by_mock
    inventario_instance = _build_inventario_instance(mocker)
    _setup_inventario_model(mocker, query=query_mock, instance=inventario_instance)
    mock_db.commit.side_effect = Exception('Unexpected error')

    with pytest.raises(ValidationError):
        crear_inventario(sample_inventario_data)

    mock_db.rollback.assert_called_once()


def test_listar_inventarios_applies_filters(mocker):
    query_mock = mocker.MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.offset.return_value = query_mock
    # Add producto_id to mocked objects
    inventories = [SimpleNamespace(id='1', producto_id=1), SimpleNamespace(id='2', producto_id=2)]
    query_mock.all.return_value = inventories
    _setup_inventario_model(mocker, query=query_mock)
    to_dict_spy = mocker.patch('app.services.inventarios_service._to_dict', side_effect=lambda x: {'id': x.id})
    
    # Mock _obtener_info_producto to avoid external calls
    mocker.patch('app.services.inventarios_service._obtener_info_producto', return_value={'nombre': 'Test', 'sku': 'SKU-123'})

    result = listar_inventarios(producto_id=1, ubicacion='Bodega', limite=50, offset=10)

    # Verify result structure includes new fields
    assert len(result) == 2
    assert result[0]['id'] == '1'
    assert result[0]['productoNombre'] == 'Test'
    assert result[0]['productoSku'] == 'SKU-123'
    
    assert query_mock.filter.call_count == 2
    query_mock.limit.assert_called_once_with(50)
    query_mock.offset.assert_called_once_with(10)
    assert to_dict_spy.call_count == 2


def test_obtener_inventario_por_id_not_found(mocker):
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = None
    _setup_inventario_model(mocker, query=query_mock)

    with pytest.raises(NotFoundError):
        obtener_inventario_por_id('missing-id')


def test_obtener_inventario_por_id_success(mocker):
    inventory = _build_inventario_instance(mocker)
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    _setup_inventario_model(mocker, query=query_mock)
    to_dict_spy = mocker.patch('app.services.inventarios_service._to_dict', return_value={'id': inventory.id})
    
    # Mock _obtener_info_producto
    mocker.patch('app.services.inventarios_service._obtener_info_producto', return_value={'nombre': 'Test', 'sku': 'SKU-123'})

    result = obtener_inventario_por_id('existing-id')

    assert result == {'id': 'test-uuid', 'productoNombre': 'Test', 'productoSku': 'SKU-123'}
    to_dict_spy.assert_called_once_with(inventory)




def test_actualizar_inventario_raises_conflict_on_duplicate_ubicacion(mocker):
    inventory = _build_inventario_instance(mocker, ubicacion='A')
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    conflict_query = mocker.MagicMock()
    conflict_query.first.return_value = object()
    query_mock.filter_by.return_value = conflict_query
    _setup_inventario_model(mocker, query=query_mock, instance=inventory)

    with pytest.raises(ConflictError):
        actualizar_inventario('inv-id', {'ubicacion': 'B'})


def test_eliminar_inventario_success(mocker, mock_db):
    inventory = _build_inventario_instance(mocker)
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    model_mock, _ = _setup_inventario_model(mocker, query=query_mock, instance=inventory)
    queue_spy = mocker.patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')

    eliminar_inventario('inv-id')

    mock_db.delete.assert_called_once_with(inventory)
    mock_db.commit.assert_called_once()
    queue_spy.assert_called_once_with(
        producto_id=inventory.producto_id,
        action='delete',
        data={'inventarioId': 'inv-id'},
    )
    model_mock.return_value  # silence unused variable warning


def test_eliminar_inventario_not_found(mocker):
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = None
    _setup_inventario_model(mocker, query=query_mock)

    with pytest.raises(NotFoundError):
        eliminar_inventario('missing-id')


def test_eliminar_inventario_generic_exception(mocker, mock_db):
    inventory = _build_inventario_instance(mocker)
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    _setup_inventario_model(mocker, query=query_mock, instance=inventory)
    mock_db.commit.side_effect = Exception('Unexpected error')

    with pytest.raises(ValidationError):
        eliminar_inventario('inv-id')
    
    mock_db.rollback.assert_called_once()


def test_ajustar_cantidad_success(mocker, mock_db):
    inventory = _build_inventario_instance(mocker, cantidad=10)
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    _setup_inventario_model(mocker, query=query_mock, instance=inventory)
    to_dict_spy = mocker.patch('app.services.inventarios_service._to_dict', return_value={'cantidad': 15})
    queue_spy = mocker.patch('app.services.inventarios_service.RedisQueueService.enqueue_cache_update')

    result = ajustar_cantidad('inv-id', 5, usuario='updater')

    assert result == {'cantidad': 15}
    assert inventory.cantidad == 15
    assert inventory.usuario_actualizacion == 'updater'
    mock_db.commit.assert_called_once()
    queue_spy.assert_called_once()
    to_dict_spy.assert_called_once_with(inventory)


def test_ajustar_cantidad_negative_result(mocker):
    inventory = _build_inventario_instance(mocker, cantidad=3)
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    _setup_inventario_model(mocker, query=query_mock, instance=inventory)

    with pytest.raises(ValidationError):
        ajustar_cantidad('inv-id', -5)


def test_ajustar_cantidad_not_found(mocker):
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = None
    _setup_inventario_model(mocker, query=query_mock)

    with pytest.raises(NotFoundError):
        ajustar_cantidad('missing-id', 5)


def test_ajustar_cantidad_generic_exception(mocker, mock_db):
    inventory = _build_inventario_instance(mocker, cantidad=10)
    query_mock = mocker.MagicMock()
    query_mock.get.return_value = inventory
    _setup_inventario_model(mocker, query=query_mock, instance=inventory)
    mock_db.commit.side_effect = Exception('Unexpected error')

    with pytest.raises(ValidationError):
        ajustar_cantidad('inv-id', 5)
    
    mock_db.rollback.assert_called_once()
