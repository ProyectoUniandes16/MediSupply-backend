import pytest
from src.services.cliente_service import register_cliente, ClienteServiceError
from src.models.cliente import Cliente

@pytest.fixture
def valid_data():
    return {
        'nombre': 'Empresa S.A.',
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'luis@empresa.com',
        'correo_empresa': 'contacto@empresa.com',
        'telefono_contacto': '5512345678',
        'nit': 'A12345678',
        'direccion': 'Calle Falsa 123'
    }


def test_datos_no_proporcionados():
    with pytest.raises(ClienteServiceError) as exc:
        register_cliente(None)
    assert exc.value.status_code == 400
    assert 'No se proporcionaron datos' in str(exc.value.message)


def test_campos_faltantes():
    data = {
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'luis@empresa.com',
        'telefono_contacto': '5512345678',
        'nit': 'A12345678',
        'direccion': 'Calle Falsa 123'
    }
    with pytest.raises(ClienteServiceError) as exc:
        register_cliente(data)
    assert exc.value.status_code == 400
    assert 'Campos faltantes' in str(exc.value.message)


def test_formato_email_invalido():
    data = {
        'nombre': 'Empresa S.A.',
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'emailinvalido',
        'correo_empresa': 'contacto@empresa.com',
        'telefono_contacto': '5512345678',
        'nit': 'A12345678',
        'direccion': 'Calle Falsa 123'
    }
    with pytest.raises(ClienteServiceError) as exc:
        register_cliente(data)
    assert exc.value.status_code == 400
    assert 'FORMATO_EMAIL_INVALIDO' in str(exc.value.message)


def test_email_ya_existe(app, mocker, valid_data):
    with app.app_context():
        # Mock the query inside the service module to simulate existing email
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mocker.Mock(first=lambda: True)
        mocker.patch('src.services.cliente_service.Cliente.query', new=mock_query)
        with pytest.raises(ClienteServiceError) as exc:
            register_cliente(valid_data)
        assert exc.value.status_code == 409
        assert 'CONTACTO_YA_EXISTE' in str(exc.value.message)


def test_telefono_corto(app, mocker):
    data = {
        'nombre': 'Empresa S.A.',
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'luis@empresa.com',
        'correo_empresa': 'contacto@empresa.com',
        'telefono_contacto': '1234',
        'nit': 'A12345678',
        'direccion': 'Calle Falsa 123'
    }
    with app.app_context():
        # Ensure no existing email/nit interferes
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mocker.Mock(first=lambda: None)
        mocker.patch('src.services.cliente_service.Cliente.query', new=mock_query)
        with pytest.raises(ClienteServiceError) as exc:
            register_cliente(data)
    assert exc.value.status_code == 400
    assert 'TELEFONO_CORTO' in str(exc.value.message)


def test_telefono_no_numerico(app, mocker):
    data = {
        'nombre': 'Empresa S.A.',
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'luis@empresa.com',
        'correo_empresa': 'contacto@empresa.com',
        'telefono_contacto': 'X1234567',
        'nit': 'A12345678',
        'direccion': 'Calle Falsa 123'
    }
    with app.app_context():
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mocker.Mock(first=lambda: None)
        mocker.patch('src.services.cliente_service.Cliente.query', new=mock_query)
        with pytest.raises(ClienteServiceError) as exc:
            register_cliente(data)
    assert exc.value.status_code == 400
    assert 'TELEFONO_NO_NUMERICO' in str(exc.value.message)


def test_nit_corto_o_largo(app, mocker):
    data = {
        'nombre': 'Empresa S.A.',
        'tipo': 'Sociedad',
        'pais': 'México',
        'nombre_contacto': 'Luis García',
        'cargo_contacto': 'Director',
        'correo_contacto': 'luis@empresa.com',
        'correo_empresa': 'contacto@empresa.com',
        'telefono_contacto': '5512345678',
        'nit': '1234',
        'direccion': 'Calle Falsa 123'
    }
    with app.app_context():
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mocker.Mock(first=lambda: None)
        mocker.patch('src.services.cliente_service.Cliente.query', new=mock_query)
        with pytest.raises(ClienteServiceError) as exc:
            register_cliente(data)
    assert exc.value.status_code == 400
    assert 'NIT_CORTO_LARGO' in str(exc.value.message)


def test_nit_ya_existe(app, mocker, valid_data):
    with app.app_context():
        # Simulate: email does NOT exist for the new email, but NIT does exist
        def filter_by_side_effect(**kwargs):
            if 'correo_contacto' in kwargs:
                return mocker.Mock(first=lambda: None)
            if 'nit' in kwargs:
                return mocker.Mock(first=lambda: True)
            return mocker.Mock(first=lambda: None)
        mock_query = mocker.Mock()
        mock_query.filter_by.side_effect = filter_by_side_effect
        mocker.patch('src.services.cliente_service.Cliente.query', new=mock_query)
        data = valid_data.copy()
        data['correo_contacto'] = 'nuevo@email.com'
        with pytest.raises(ClienteServiceError) as exc:
            register_cliente(data)
        assert exc.value.status_code == 409
        assert 'CLIENTE_YA_EXISTE' in str(exc.value.message)


def test_exito_creacion_cliente(app, mocker, valid_data):
    with app.app_context():
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mocker.Mock(first=lambda: None)

        # build a real instance but override its save and to_dict
        cliente_mock = Cliente(**valid_data)
        cliente_mock.save = lambda: None
        cliente_mock.to_dict = lambda: {'id': 1, 'nombre': valid_data['nombre']}

        # create a fake class with query attribute that returns the instance when called
        fake_cliente_class = mocker.Mock(return_value=cliente_mock)
        fake_cliente_class.query = mock_query
        mocker.patch('src.services.cliente_service.Cliente', new=fake_cliente_class)

        result = register_cliente(valid_data)
        assert 'cliente' in result['data']
        assert result['data']['cliente']['nombre'] == valid_data['nombre']
        assert result['data']['message'] == 'Cliente creado exitosamente'


def test_error_al_guardar_cliente(app, mocker, valid_data):
    with app.app_context():
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mocker.Mock(first=lambda: None)

        cliente_mock = Cliente(**valid_data)
        def raise_exception():
            raise RuntimeError("Error BD")
        cliente_mock.save = lambda: (_ for _ in ()).throw(RuntimeError("Error BD"))
        mocker.patch('src.services.cliente_service.Cliente', new=mocker.Mock(return_value=cliente_mock))
        # ensure the patched class has a query attribute
        src_cliente = __import__('src.services.cliente_service', fromlist=['Cliente'])
        setattr(src_cliente.Cliente, 'query', mock_query)

        with pytest.raises(ClienteServiceError) as exc:
            register_cliente(valid_data)
        assert exc.value.status_code == 500
        assert 'ERROR_CREAR_CLIENTE' in str(exc.value.message)
