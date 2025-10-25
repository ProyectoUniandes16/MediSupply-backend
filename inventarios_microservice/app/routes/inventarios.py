from flask import Blueprint, request, jsonify
from app.services import inventarios_service
from app.services import ValidationError, NotFoundError, ConflictError

bp_inventarios = Blueprint("inventarios", __name__)


@bp_inventarios.route("", methods=["POST"])
def crear_inventario():
    """Crea un nuevo inventario."""
    try:
        data = request.get_json()
        data.ubicacion = "111111"
        resultado = inventarios_service.crear_inventario(data)
        return jsonify(resultado), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except ConflictError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp_inventarios.route("", methods=["GET"])
def listar_inventarios():
    """Lista todos los inventarios con filtros opcionales."""
    try:
        # Obtener parámetros de query
        producto_id = request.args.get("productoId")
        ubicacion = request.args.get("ubicacion")
        limite = request.args.get("limite", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        # Validar límites razonables
        if limite > 1000:
            limite = 1000
        if limite < 1:
            limite = 100
        if offset < 0:
            offset = 0
        
        inventarios = inventarios_service.listar_inventarios(
            producto_id=producto_id,
            ubicacion=ubicacion,
            limite=limite,
            offset=offset
        )
        
        return jsonify({
            "inventarios": inventarios,
            "total": len(inventarios),
            "limite": limite,
            "offset": offset
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp_inventarios.route("/<inventario_id>", methods=["GET"])
def obtener_inventario(inventario_id):
    """Obtiene un inventario por su ID."""
    try:
        inventario = inventarios_service.obtener_inventario_por_id(inventario_id)
        return jsonify(inventario), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp_inventarios.route("/<inventario_id>", methods=["PUT"])
def actualizar_inventario(inventario_id):
    """Actualiza un inventario existente."""
    try:
        data = request.get_json()
        inventario = inventarios_service.actualizar_inventario(inventario_id, data)
        return jsonify(inventario), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except ConflictError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp_inventarios.route("/<inventario_id>", methods=["PATCH"])
def actualizar_parcial_inventario(inventario_id):
    """Actualiza parcialmente un inventario (alias de PUT para compatibilidad)."""
    return actualizar_inventario(inventario_id)


@bp_inventarios.route("/<inventario_id>", methods=["DELETE"])
def eliminar_inventario(inventario_id):
    """Elimina un inventario por su ID."""
    try:
        inventarios_service.eliminar_inventario(inventario_id)
        return jsonify({"mensaje": "Inventario eliminado exitosamente"}), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp_inventarios.route("/<inventario_id>/ajustar", methods=["POST"])
def ajustar_cantidad(inventario_id):
    """Ajusta la cantidad de un inventario (suma o resta)."""
    try:
        data = request.get_json()
        
        if "ajuste" not in data:
            return jsonify({"error": "El campo 'ajuste' es obligatorio"}), 400
        
        ajuste = data.get("ajuste")
        usuario = data.get("usuario")
        
        if not isinstance(ajuste, int):
            return jsonify({"error": "El campo 'ajuste' debe ser un número entero"}), 400
        
        inventario = inventarios_service.ajustar_cantidad(inventario_id, ajuste, usuario)
        return jsonify(inventario), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp_inventarios.route("/producto/<producto_id>", methods=["GET"])
def obtener_inventarios_por_producto(producto_id):
    """Obtiene todos los inventarios de un producto específico."""
    try:
        inventarios = inventarios_service.listar_inventarios(producto_id=producto_id)
        return jsonify({
            "productoId": producto_id,
            "inventarios": inventarios,
            "total": len(inventarios)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
