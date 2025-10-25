"""
Rutas para gestión de Planes de Venta - KAN-86
"""
from flask import Blueprint, jsonify, request
from app.services.plan_venta_service import (
    crear_o_actualizar_plan_venta,
    obtener_plan_venta,
    listar_planes_venta
)
from app.services import ValidationError, NotFoundError, ConflictError

bp_planes_venta = Blueprint("planes_venta", __name__)


@bp_planes_venta.route("/planes-venta", methods=["POST"])
def post_plan_venta():
    """
    Crea o actualiza un plan de venta (UPSERT).
    
    Request Body:
        {
            "nombre_plan": "Plan Q1 2025",
            "gerente_id": "uuid-gerente",
            "vendedor_id": "uuid-vendedor",
            "periodo": "2025-01",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20,
            "estado": "activo"  // opcional
        }
    
    Returns:
        201: Plan creado exitosamente
        200: Plan actualizado exitosamente
        400: Error de validación
        404: Vendedor no encontrado
        409: Conflicto de concurrencia
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        data = crear_o_actualizar_plan_venta(payload)
        
        # Si fue creado, retornar 201; si fue actualizado, retornar 200
        status_code = 201 if data.get("operacion") == "crear" else 200
        
        return jsonify(data), status_code
        
    except ValidationError as e:
        return jsonify(e.message), 400
    except NotFoundError as e:
        return jsonify(e.message), 404
    except ConflictError as e:
        return jsonify(e.message), 409
    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO",
            "detalle": str(e)
        }), 500


@bp_planes_venta.route("/planes-venta/<string:plan_id>", methods=["GET"])
def get_plan_venta(plan_id: str):
    """
    Obtiene un plan de venta por su ID.
    
    Args:
        plan_id: ID del plan
        
    Returns:
        200: Plan encontrado
        404: Plan no encontrado
    """
    try:
        data = obtener_plan_venta(plan_id)
        return jsonify(data), 200
    except NotFoundError as e:
        return jsonify(e.message), 404
    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO"
        }), 500


@bp_planes_venta.route("/planes-venta", methods=["GET"])
def get_planes_venta():
    """
    Lista planes de venta con filtros opcionales.
    
    Query Parameters:
        - vendedor_id: Filtrar por vendedor
        - periodo: Filtrar por periodo (YYYY-MM)
        - estado: Filtrar por estado
        - page: Número de página (default: 1)
        - size: Tamaño de página (default: 10)
        
    Returns:
        200: Lista de planes
    """
    try:
        vendedor_id = request.args.get("vendedor_id")
        periodo = request.args.get("periodo")
        estado = request.args.get("estado")
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 10))
        
        # Validar page y size
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10
        
        data = listar_planes_venta(
            vendedor_id=vendedor_id,
            periodo=periodo,
            estado=estado,
            page=page,
            size=size
        )
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO",
            "detalle": str(e)
        }), 500
