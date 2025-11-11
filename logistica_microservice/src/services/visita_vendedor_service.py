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


def listar_visitas_vendedor(vendedor_id, fecha_inicio=None, fecha_fin=None):
    """Lista visitas para un vendedor con opción de filtrar por rango de fechas."""
    if vendedor_id is None:
        raise VisitaVendedorServiceError(
            {
                "error": "Debe proporcionar el vendedor_id",
                "codigo": "VENDEDOR_ID_REQUERIDO",
            },
            400,
        )

    if not isinstance(vendedor_id, str) or not vendedor_id.strip():
        raise VisitaVendedorServiceError(
            {
                "error": "vendedor_id debe ser una cadena no vacía",
                "codigo": "VENDEDOR_ID_INVALIDO",
            },
            400,
        )
    vendedor_normalizado = vendedor_id.strip()

    fecha_inicio_parseada = None
    fecha_fin_parseada = None
    if (fecha_inicio and not fecha_fin) or (fecha_fin and not fecha_inicio):
        raise VisitaVendedorServiceError(
            {
                "error": "Debe proporcionar fecha_inicio y fecha_fin para el rango",
                "codigo": "RANGO_FECHAS_INCOMPLETO",
            },
            400,
        )

    if fecha_inicio and fecha_fin:
        fecha_inicio_parseada = _parse_fecha_visita(fecha_inicio)
        fecha_fin_parseada = _parse_fecha_visita(fecha_fin)

        if fecha_inicio_parseada > fecha_fin_parseada:
            raise VisitaVendedorServiceError(
                {
                    "error": "fecha_inicio no puede ser mayor que fecha_fin",
                    "codigo": "RANGO_FECHAS_INVALIDO",
                },
                400,
            )

    try:
        query = VisitaVendedor.query.filter_by(vendedor_id=vendedor_normalizado)

        if fecha_inicio_parseada and fecha_fin_parseada:
            query = query.filter(VisitaVendedor.fecha_visita >= fecha_inicio_parseada)
            query = query.filter(VisitaVendedor.fecha_visita <= fecha_fin_parseada)

        visitas = (
            query.order_by(VisitaVendedor.fecha_visita.asc(), VisitaVendedor.id.asc())
            .all()
        )

        return [
            {
                "id_visita": visita.id,
                "cliente_id": visita.cliente_id,
                "vendedor_id": visita.vendedor_id,
                "fecha_visita": visita.fecha_visita.isoformat(),
                "estado": visita.estado,
            }
            for visita in visitas
        ]
    except VisitaVendedorServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error("Error al listar visitas de vendedor: %s", str(exc))
        raise VisitaVendedorServiceError(
            {
                "error": "Error al listar las visitas",
                "codigo": "ERROR_LISTAR_VISITAS",
            },
            500,
        )


def actualizar_visita_vendedor(visita_id, data):
    """Actualiza estado y observación de una visita."""
    if data is None:
        raise VisitaVendedorServiceError(
            {"error": "No se proporcionaron datos"},
            400,
        )

    estado = data.get("estado")
    if estado is None:
        raise VisitaVendedorServiceError(
            {
                "error": "Debe proporcionar el estado",
                "codigo": "ESTADO_REQUERIDO",
            },
            400,
        )

    if estado not in VALID_ESTADOS_VISITA:
        raise VisitaVendedorServiceError(
            {
                "error": "Estado inválido. Valores permitidos: pendiente, en progreso, finalizado",
                "codigo": "ESTADO_INVALIDO",
            },
            400,
        )

    comentarios_presentes = "comentarios" in data
    comentarios_actualizados = None
    if comentarios_presentes:
        comentarios_actualizados = data.get("comentarios")
        if comentarios_actualizados is not None and not isinstance(comentarios_actualizados, str):
            raise VisitaVendedorServiceError(
                {
                    "error": "comentarios debe ser una cadena",
                    "codigo": "COMENTARIOS_INVALIDOS",
                },
                400,
            )
        if isinstance(comentarios_actualizados, str):
            comentarios_actualizados = comentarios_actualizados.strip()
            if comentarios_actualizados == "":
                comentarios_actualizados = None

    try:
        visita = db.session.get(VisitaVendedor, visita_id)
        if visita is None:
            raise VisitaVendedorServiceError(
                {
                    "error": "Visita no encontrada",
                    "codigo": "VISITA_NO_ENCONTRADA",
                },
                404,
            )

        visita.estado = estado
        if comentarios_presentes:
            visita.comentarios = comentarios_actualizados

        db.session.commit()
        current_app.logger.info(
            "Visita actualizada: visita_id=%s nuevo_estado=%s",
            visita_id,
            estado,
        )
        return visita.to_dict()
    except VisitaVendedorServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensivo
        db.session.rollback()
        current_app.logger.error("Error al actualizar visita de vendedor: %s", str(exc))
        raise VisitaVendedorServiceError(
            {
                "error": "Error al actualizar la visita",
                "codigo": "ERROR_ACTUALIZAR_VISITA",
            },
            500,
        )
