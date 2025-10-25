from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.models import db
from app.models.inventario import Inventario
from app.utils.validators import require, is_positive_integer, length_between
from . import NotFoundError, ConflictError, ValidationError

def _to_dict(i: Inventario) -> Dict[str, Any]:
    """Convierte un inventario a diccionario para la respuesta JSON."""
    return {
        "id": i.id,
        "productoId": i.producto_id,
        "cantidad": i.cantidad,
        "ubicacion": i.ubicacion,
        "usuarioCreacion": i.usuario_creacion,
        "fechaCreacion": i.fecha_creacion.isoformat() if i.fecha_creacion else None,
        "usuarioActualizacion": i.usuario_actualizacion,
        "fechaActualizacion": i.fecha_actualizacion.isoformat() if i.fecha_actualizacion else None,
    }


def crear_inventario(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuevo registro de inventario."""
    # Validar campos obligatorios
    require(payload, ["productoId", "cantidad", "ubicacion"])
    
    producto_id = payload.get("productoId")
    cantidad = payload.get("cantidad")
    ubicacion = payload.get("ubicacion")
    usuario = payload.get("usuario")
    
    # Validaciones específicas
    is_positive_integer(cantidad, "cantidad")
    length_between(producto_id, 1, 100, "productoId")
    length_between(ubicacion, 1, 100, "ubicacion")
    
    # Verificar si ya existe un inventario para este producto en esta ubicación
    existente = Inventario.query.filter_by(
        producto_id=producto_id,
        ubicacion="111111"
    ).first()
    
    if existente:
        raise ConflictError(
            f"Ya existe un inventario para el producto '{producto_id}' en la ubicación '{ubicacion}'"
        )
    
    # Crear nuevo inventario
    try:
        inventario = Inventario(
            id=str(uuid4()),
            producto_id=producto_id,
            cantidad=cantidad,
            ubicacion=ubicacion,
            usuario_creacion=usuario,
            usuario_actualizacion=usuario
        )
        db.session.add(inventario)
        db.session.commit()
        return _to_dict(inventario)
    except IntegrityError as e:
        db.session.rollback()
        raise ConflictError(f"Error de integridad al crear inventario: {str(e)}")
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f"Error al crear inventario: {str(e)}")


def listar_inventarios(
    producto_id: Optional[str] = None,
    ubicacion: Optional[str] = None,
    limite: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Lista todos los inventarios con filtros opcionales."""
    query = Inventario.query
    
    # Aplicar filtros si se proporcionan
    if producto_id:
        query = query.filter(Inventario.producto_id == producto_id)
    if ubicacion:
        query = query.filter(Inventario.ubicacion.ilike(f"%{ubicacion}%"))
    
    # Aplicar paginación
    inventarios = query.order_by(Inventario.fecha_creacion.desc()).limit(limite).offset(offset).all()
    
    return [_to_dict(i) for i in inventarios]


def obtener_inventario_por_id(inventario_id: str) -> Dict[str, Any]:
    """Obtiene un inventario por su ID."""
    inventario = Inventario.query.get(inventario_id)
    
    if not inventario:
        raise NotFoundError(f"Inventario con ID '{inventario_id}' no encontrado")
    
    return _to_dict(inventario)


def actualizar_inventario(inventario_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza un inventario existente."""
    inventario = Inventario.query.get(inventario_id)
    
    if not inventario:
        raise NotFoundError(f"Inventario con ID '{inventario_id}' no encontrado")
    
    # Actualizar campos permitidos
    if "cantidad" in payload:
        cantidad = payload["cantidad"]
        is_positive_integer(cantidad, "cantidad")
        inventario.cantidad = cantidad
    
    if "ubicacion" in payload:
        ubicacion = payload["ubicacion"]
        length_between(ubicacion, 1, 100, "ubicacion")
        
        # Verificar que no exista otro inventario con el mismo producto en la nueva ubicación
        if ubicacion != inventario.ubicacion:
            existente = Inventario.query.filter_by(
                producto_id=inventario.producto_id,
                ubicacion=ubicacion
            ).first()
            
            if existente:
                raise ConflictError(
                    f"Ya existe un inventario para el producto '{inventario.producto_id}' "
                    f"en la ubicación '{ubicacion}'"
                )
        
        inventario.ubicacion = ubicacion
    
    if "productoId" in payload:
        producto_id = payload["productoId"]
        length_between(producto_id, 1, 100, "productoId")
        
        # Verificar que no exista otro inventario con el nuevo producto en la misma ubicación
        if producto_id != inventario.producto_id:
            existente = Inventario.query.filter_by(
                producto_id=producto_id,
                ubicacion=inventario.ubicacion
            ).first()
            
            if existente:
                raise ConflictError(
                    f"Ya existe un inventario para el producto '{producto_id}' "
                    f"en la ubicación '{inventario.ubicacion}'"
                )
        
        inventario.producto_id = producto_id
    
    if "usuario" in payload:
        inventario.usuario_actualizacion = payload["usuario"]
    
    try:
        db.session.commit()
        return _to_dict(inventario)
    except IntegrityError as e:
        db.session.rollback()
        raise ConflictError(f"Error de integridad al actualizar inventario: {str(e)}")
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f"Error al actualizar inventario: {str(e)}")


def eliminar_inventario(inventario_id: str) -> None:
    """Elimina un inventario por su ID."""
    inventario = Inventario.query.get(inventario_id)
    
    if not inventario:
        raise NotFoundError(f"Inventario con ID '{inventario_id}' no encontrado")
    
    try:
        db.session.delete(inventario)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f"Error al eliminar inventario: {str(e)}")


def ajustar_cantidad(inventario_id: str, ajuste: int, usuario: Optional[str] = None) -> Dict[str, Any]:
    """Ajusta la cantidad de un inventario (suma o resta)."""
    inventario = Inventario.query.get(inventario_id)
    
    if not inventario:
        raise NotFoundError(f"Inventario con ID '{inventario_id}' no encontrado")
    
    nueva_cantidad = inventario.cantidad + ajuste
    
    if nueva_cantidad < 0:
        raise ValidationError(
            f"El ajuste de {ajuste} resultaría en una cantidad negativa "
            f"(cantidad actual: {inventario.cantidad})"
        )
    
    inventario.cantidad = nueva_cantidad
    
    if usuario:
        inventario.usuario_actualizacion = usuario
    
    try:
        db.session.commit()
        return _to_dict(inventario)
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f"Error al ajustar cantidad: {str(e)}")

