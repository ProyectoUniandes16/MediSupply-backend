from datetime import datetime
from flask import current_app
from sqlalchemy.exc import IntegrityError
from src.models.visita_vendedor import VisitaVendedor
from src.models.zona import db


VALID_ESTADOS_VISITA = {"pendiente", "en progreso", "finalizado"}


class VisitaVendedorServiceError(Exception):
    """Errores de la capa de servicio para visitas de vendedor."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_fecha_visita(valor):
    """Intenta parsear la fecha usando formatos comunes."""
    if not isinstance(valor, str):
        raise VisitaVendedorServiceError(
            {"error": "El campo fecha_visita debe ser una cadena"},
            400,
        )

    formatos = ("%Y-%m-%d", "%d/%m/%Y")
    for formato in formatos:
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue

    raise VisitaVendedorServiceError(
        {
            "error": "Formato de fecha inválido. Usa YYYY-MM-DD o DD/MM/YYYY",
            "codigo": "FORMATO_FECHA_INVALIDO",
        },
        400,
    )


def _parse_fecha_fin(valor):
    """Parsea fecha/hora de fin si se proporciona."""
    if valor is None or valor == "":
        return None

    if isinstance(valor, datetime):
        return valor

    if not isinstance(valor, str):
        raise VisitaVendedorServiceError(
            {"error": "El campo fecha_fin_visita debe ser una cadena o datetime"},
            400,
        )

    formatos = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
    )
    for formato in formatos:
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        raise VisitaVendedorServiceError(
            {
                "error": "Formato de fecha_fin_visita inválido",
                "codigo": "FORMATO_FIN_INVALIDO",
            },
            400,
        )


def crear_visita_vendedor(data):
    """Crea una nueva visita de vendedor."""
    if data is None:
        raise VisitaVendedorServiceError(
            {"error": "No se proporcionaron datos"},
            400,
        )

    required_fields = ["cliente_id", "vendedor_id", "fecha_visita"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise VisitaVendedorServiceError(
            {
                "error": f"Campos faltantes: {', '.join(missing)}",
                "codigo": "CAMPOS_FALTANTES",
            },
            400,
        )

    try:
        cliente_id = int(data["cliente_id"])
    except (TypeError, ValueError):
        raise VisitaVendedorServiceError(
            {
                "error": "cliente_id debe ser un número entero",
                "codigo": "CLIENTE_ID_INVALIDO",
            },
            400,
        )

    vendedor_id = data["vendedor_id"]
    if not isinstance(vendedor_id, str) or not vendedor_id:
        raise VisitaVendedorServiceError(
            {
                "error": "vendedor_id debe ser una cadena no vacía",
                "codigo": "VENDEDOR_ID_INVALIDO",
            },
            400,
        )

    fecha_visita = _parse_fecha_visita(data["fecha_visita"])

    estado = data.get("estado", "pendiente")
    if estado not in VALID_ESTADOS_VISITA:
        raise VisitaVendedorServiceError(
            {
                "error": "Estado inválido. Valores permitidos: pendiente, en progreso, finalizado",
                "codigo": "ESTADO_INVALIDO",
            },
            400,
        )

    nombre_contacto = data.get("nombre_contacto")
    if nombre_contacto is not None:
        if not isinstance(nombre_contacto, str) or not nombre_contacto.strip():
            raise VisitaVendedorServiceError(
                {
                    "error": "nombre_contacto debe ser una cadena no vacía",
                    "codigo": "NOMBRE_CONTACTO_INVALIDO",
                },
                400,
            )
        nombre_contacto = nombre_contacto.strip()

    latitud = data.get("latitud")
    longitud = data.get("longitud")
    if latitud is not None or longitud is not None:
        if latitud is None or longitud is None:
            raise VisitaVendedorServiceError(
                {
                    "error": "Debe proporcionar latitud y longitud juntas",
                    "codigo": "GEO_INCOMPLETA",
                },
                400,
            )
        try:
            latitud = float(latitud)
            longitud = float(longitud)
        except (TypeError, ValueError):
            raise VisitaVendedorServiceError(
                {
                    "error": "Latitud y longitud deben ser números",
                    "codigo": "GEO_INVALIDA",
                },
                400,
            )
        if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
            raise VisitaVendedorServiceError(
                {
                    "error": "Latitud/longitud fuera de rango",
                    "codigo": "GEO_FUERA_RANGO",
                },
                400,
            )

    fecha_fin_visita = _parse_fecha_fin(data.get("fecha_fin_visita"))

    comentarios = data.get("comentarios")
    if comentarios is not None:
        if not isinstance(comentarios, str):
            raise VisitaVendedorServiceError(
                {
                    "error": "comentarios debe ser una cadena",
                    "codigo": "COMENTARIOS_INVALIDOS",
                },
                400,
            )
        comentarios = comentarios.strip()
        if comentarios == "":
            comentarios = None

    try:
        visita = VisitaVendedor(
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            fecha_visita=fecha_visita,
            estado=estado,
            nombre_contacto=nombre_contacto,
            latitud=latitud,
            longitud=longitud,
            fecha_fin_visita=fecha_fin_visita,
            comentarios=comentarios,
        )
        visita.save()
        current_app.logger.info(
            "Visita de vendedor creada: vendedor_id=%s cliente_id=%s fecha_visita=%s",
            vendedor_id,
            cliente_id,
            fecha_visita.isoformat(),
        )
        return visita.to_dict()
    except IntegrityError as exc:
        db.session.rollback()
        current_app.logger.warning(
            "Visita duplicada para vendedor_id=%s cliente_id=%s fecha_visita=%s: %s",
            vendedor_id,
            cliente_id,
            fecha_visita.isoformat(),
            str(exc),
        )
        raise VisitaVendedorServiceError(
            {
                "error": "Ya existe una visita para este vendedor, cliente y fecha",
                "codigo": "VISITA_DUPLICADA",
            },
            409,
        )
    except VisitaVendedorServiceError:
        raise
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Error al guardar la visita de vendedor: %s", str(exc))
        raise VisitaVendedorServiceError(
            {
                "error": "Error al guardar la visita",
                "codigo": "ERROR_GUARDAR_VISITA",
            },
            500,
        )
