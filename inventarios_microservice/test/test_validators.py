import pytest
from app.utils.validators import require, is_required, is_positive_integer, is_non_negative_integer
from app.utils.validators import length_between, is_valid_email, is_valid_uuid, is_in_range, is_alphanumeric, ValidationError

class TestValidators:

    def test_require_success(self):
        payload = {'a': 1, 'b': 'test'}
        require(payload, ['a', 'b'])

    def test_require_failure(self):
        payload = {'a': 1}
        with pytest.raises(ValidationError) as exc:
            require(payload, ['a', 'b'])
        assert "Faltan campos obligatorios: b" in str(exc.value)

    def test_is_required_success(self):
        is_required('value', 'field')

    def test_is_required_failure(self):
        with pytest.raises(ValidationError) as exc:
            is_required(None, 'field')
        assert "El campo 'field' es obligatorio" in str(exc.value)

    def test_is_positive_integer_success(self):
        is_positive_integer(1, 'field')

    def test_is_positive_integer_failure_type(self):
        with pytest.raises(ValidationError) as exc:
            is_positive_integer('1', 'field')
        assert "debe ser un entero positivo" in str(exc.value)

    def test_is_positive_integer_failure_value(self):
        with pytest.raises(ValidationError) as exc:
            is_positive_integer(0, 'field')
        assert "debe ser un entero positivo" in str(exc.value)

    def test_is_non_negative_integer_success(self):
        is_non_negative_integer(0, 'field')
        is_non_negative_integer(1, 'field')

    def test_is_non_negative_integer_failure(self):
        with pytest.raises(ValidationError) as exc:
            is_non_negative_integer(-1, 'field')
        assert "debe ser un entero no negativo" in str(exc.value)

    def test_length_between_success(self):
        length_between("abc", 1, 5, 'field')

    def test_length_between_failure_type(self):
        with pytest.raises(ValidationError) as exc:
            length_between(123, 1, 5, 'field')
        assert "debe ser una cadena de texto" in str(exc.value)

    def test_length_between_failure_length(self):
        with pytest.raises(ValidationError) as exc:
            length_between("abcdef", 1, 5, 'field')
        assert "debe tener entre 1 y 5 caracteres" in str(exc.value)

    def test_is_valid_email_success(self):
        is_valid_email("test@example.com", 'field')

    def test_is_valid_email_failure(self):
        with pytest.raises(ValidationError) as exc:
            is_valid_email("invalid-email", 'field')
        assert "debe ser un email válido" in str(exc.value)

    def test_is_valid_uuid_success(self):
        is_valid_uuid("550e8400-e29b-41d4-a716-446655440000", 'field')

    def test_is_valid_uuid_failure(self):
        with pytest.raises(ValidationError) as exc:
            is_valid_uuid("invalid-uuid", 'field')
        assert "debe ser un UUID válido" in str(exc.value)

    def test_is_in_range_success(self):
        is_in_range(5, 1, 10, 'field')

    def test_is_in_range_failure_type(self):
        with pytest.raises(ValidationError) as exc:
            is_in_range("5", 1, 10, 'field')
        assert "debe ser un número entero" in str(exc.value)

    def test_is_in_range_failure_value(self):
        with pytest.raises(ValidationError) as exc:
            is_in_range(11, 1, 10, 'field')
        assert "debe estar entre 1 y 10" in str(exc.value)

    def test_is_alphanumeric_success(self):
        is_alphanumeric("abc-123_DEF", 'field')

    def test_is_alphanumeric_failure(self):
        with pytest.raises(ValidationError) as exc:
            is_alphanumeric("abc@123", 'field')
        assert "debe ser alfanumérico" in str(exc.value)
