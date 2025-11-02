from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.models import db
from app.models.inventario import Inventario
from app.utils.validators import require, is_positive_integer, length_between
from app.services.redis_queue_service import RedisQueueService
from . import NotFoundError, ConflictError, ValidationError
import logging

logger = logging.getLogger(__name__)

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
    length_between(ubicacion, 1, 100, "ubicacion")
    
    # producto_id debe ser un entero positivo (FK a productos.id)
    if not isinstance(producto_id, int) or producto_id <= 0:
        raise ValidationError("El campo 'productoId' debe ser un entero positivo")
    
    # Verificar si ya existe un inventario para este producto en esta ubicación
    existente = Inventario.query.filter_by(
        producto_id=producto_id,
        ubicacion=ubicacion
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
        
        # Encolar actualización de cache
        RedisQueueService.enqueue_cache_update(
            producto_id=producto_id,
            action='create',
            data=_to_dict(inventario)
        )
        
        logger.info(f"✅ Inventario creado: {inventario.id}")
        return _to_dict(inventario)
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # Detectar error de Foreign Key (producto no existe)
        if 'foreign key constraint' in error_msg.lower() or 'fk_' in error_msg.lower():
            raise NotFoundError(f"El producto con ID '{producto_id}' no existe")
        
        # Detectar error de constraint único (ya existe inventario en esa ubicación)
        if 'unique constraint' in error_msg.lower() or 'uq_producto_ubicacion' in error_msg.lower():
            raise ConflictError(
                f"Ya existe un inventario para el producto '{producto_id}' en la ubicación '{ubicacion}'"
            )
        
        raise ConflictError(f"Error de integridad: {error_msg}")
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
        
        # producto_id debe ser un entero positivo
        if not isinstance(producto_id, int) or producto_id <= 0:
            raise ValidationError("El campo 'productoId' debe ser un entero positivo")
        
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
        
        # Encolar actualización de cache
        RedisQueueService.enqueue_cache_update(
            producto_id=inventario.producto_id,
            action='update',
            data=_to_dict(inventario)
        )
        
        logger.info(f"✅ Inventario actualizado: {inventario_id}")
        return _to_dict(inventario)
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # Detectar error de Foreign Key (producto no existe)
        if 'foreign key constraint' in error_msg.lower() or 'fk_' in error_msg.lower():
            raise NotFoundError(f"El producto con ID '{payload.get('productoId')}' no existe")
        
        # Detectar error de constraint único
        if 'unique constraint' in error_msg.lower() or 'uq_producto_ubicacion' in error_msg.lower():
            raise ConflictError(
                f"Ya existe un inventario para ese producto en la ubicación especificada"
            )
        
        raise ConflictError(f"Error de integridad: {error_msg}")
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f"Error al actualizar inventario: {str(e)}")


def eliminar_inventario(inventario_id: str) -> None:
    """Elimina un inventario por su ID."""
    inventario = Inventario.query.get(inventario_id)
    
    if not inventario:
        raise NotFoundError(f"Inventario con ID '{inventario_id}' no encontrado")
    
    producto_id = inventario.producto_id  # Guardar antes de eliminar
    
    try:
        db.session.delete(inventario)
        db.session.commit()
        
        # Encolar actualización de cache
        RedisQueueService.enqueue_cache_update(
            producto_id=producto_id,
            action='delete',
            data={'inventarioId': inventario_id}
        )
        
        logger.info(f"✅ Inventario eliminado: {inventario_id}")
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
        
        # Encolar actualización de cache
        RedisQueueService.enqueue_cache_update(
            producto_id=inventario.producto_id,
            action='adjust',
            data={
                'inventarioId': inventario_id,
                'ajuste': ajuste,
                'nuevaCantidad': nueva_cantidad
            }
        )
        
        logger.info(f"✅ Cantidad ajustada: {inventario_id} ({ajuste:+d})")
        return _to_dict(inventario)
    except Exception as e:
        db.session.rollback()
        raise ValidationError(f"Error al ajustar cantidad: {str(e)}")

