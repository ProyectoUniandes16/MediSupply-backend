import re
from datetime import date
from typing import Any
from uuid import UUID
from .errors import ValidationError


def require(payload: dict, fields: list[str]) -> None:
    """Exige que existan y no sean vacíos (None/''/[]) los campos indicados."""
    missing = [f for f in fields if payload.get(f) in (None, "", [])]
    if missing:
        raise ValidationError(f"Faltan campos obligatorios: {', '.join(missing)}")


def is_required(value: Any, field_name: str) -> None:
    """Valida que un campo sea obligatorio."""
    if value is None:
        raise ValidationError(f"El campo '{field_name}' es obligatorio.")


def is_positive_integer(value: Any, field_name: str) -> None:
    """Valida que un campo sea un entero positivo."""
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"El campo '{field_name}' debe ser un entero positivo.")


def is_non_negative_integer(value: Any, field_name: str) -> None:
    """Valida que un campo sea un entero no negativo (>= 0)."""
    if not isinstance(value, int) or value < 0:
        raise ValidationError(f"El campo '{field_name}' debe ser un entero no negativo.")


def length_between(value: str, min_length: int, max_length: int, field_name: str) -> None:
    """Valida que la longitud de un campo esté entre los límites especificados."""
    if not isinstance(value, str):
        raise ValidationError(f"El campo '{field_name}' debe ser una cadena de texto.")
    if not (min_length <= len(value) <= max_length):
        raise ValidationError(f"El campo '{field_name}' debe tener entre {min_length} y {max_length} caracteres.")


def is_valid_email(value: str, field_name: str) -> None:
    """Valida que un campo sea un email válido."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValidationError(f"El campo '{field_name}' debe ser un email válido.")


def is_valid_uuid(value: str, field_name: str) -> None:
    """Valida que un campo sea un UUID válido."""
    try:
        UUID(value)
    except (ValueError, AttributeError):
        raise ValidationError(f"El campo '{field_name}' debe ser un UUID válido.")


def is_in_range(value: int, min_val: int, max_val: int, field_name: str) -> None:
    """Valida que un valor esté dentro de un rango específico."""
    if not isinstance(value, int):
        raise ValidationError(f"El campo '{field_name}' debe ser un número entero.")
    if not (min_val <= value <= max_val):
        raise ValidationError(f"El campo '{field_name}' debe estar entre {min_val} y {max_val}.")


def is_alphanumeric(value: str, field_name: str) -> None:
    """Valida que un campo sea alfanumérico."""
    if not value.replace("-", "").replace("_", "").isalnum():
        raise ValidationError(f"El campo '{field_name}' debe ser alfanumérico (se permiten guiones y guiones bajos).")
