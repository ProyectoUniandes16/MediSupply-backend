"""
Servicio de Plan de Venta - KAN-86
Gestión de planes de venta con operación UPSERT (create or update).
"""
from typing import Dict, Any
from uuid import uuid4
from decimal import Decimal, InvalidOperation
import re
from sqlalchemy.exc import IntegrityError
from app.models import db
from app.models.plan_venta import PlanVenta
from app.models.vendedor import Vendedor
from app.utils.validators import require
from . import NotFoundError, ConflictError, ValidationError


def validar_periodo(periodo: str) -> None:
    """
    Valida que el periodo tenga formato YYYY-MM.
    
    Args:
        periodo: String con formato esperado YYYY-MM
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not periodo or not isinstance(periodo, str):
        raise ValidationError({
            "error": "El periodo es requerido",
            "codigo": "PERIODO_REQUERIDO"
        })
    
    # Validar formato YYYY-MM con regex
    pattern = r'^\d{4}-(0[1-9]|1[0-2])$'
    if not re.match(pattern, periodo):
        raise ValidationError({
            "error": "Formato de periodo inválido. Use YYYY-MM (ejemplo: 2025-01)",
            "codigo": "FORMATO_PERIODO_INVALIDO",
            "campo": "periodo"
        })
    
    # Validar año razonable (entre 2020 y 2050)
    year = int(periodo.split('-')[0])
    if year < 2020 or year > 2050:
        raise ValidationError({
            "error": "El año debe estar entre 2020 y 2050",
            "codigo": "ANIO_FUERA_DE_RANGO",
            "campo": "periodo"
        })


def validar_decimal_no_negativo(valor: Any, campo: str) -> Decimal:
    """
    Valida que un valor sea decimal/entero y no negativo.
    
    Args:
        valor: Valor a validar
        campo: Nombre del campo para mensajes de error
        
    Returns:
        Decimal: Valor convertido a Decimal
        
    Raises:
        ValidationError: Si el valor es inválido
    """
    if valor is None:
        raise ValidationError({
            "error": f"El campo {campo} es requerido",
            "codigo": "CAMPO_REQUERIDO",
            "campo": campo
        })
    
    try:
        valor_decimal = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError({
            "error": f"El campo {campo} debe ser un número válido",
            "codigo": "FORMATO_NUMERICO_INVALIDO",
            "campo": campo
        })
    
    if valor_decimal < 0:
        raise ValidationError({
            "error": f"El campo {campo} no puede ser negativo",
            "codigo": "VALOR_NEGATIVO",
            "campo": campo
        })
    
    return valor_decimal


def validar_entero_no_negativo(valor: Any, campo: str) -> int:
    """
    Valida que un valor sea entero y no negativo.
    
    Args:
        valor: Valor a validar
        campo: Nombre del campo para mensajes de error
        
    Returns:
        int: Valor convertido a entero
        
    Raises:
        ValidationError: Si el valor es inválido
    """
    if valor is None:
        raise ValidationError({
            "error": f"El campo {campo} es requerido",
            "codigo": "CAMPO_REQUERIDO",
            "campo": campo
        })
    
    try:
        valor_int = int(valor)
    except (ValueError, TypeError):
        raise ValidationError({
            "error": f"El campo {campo} debe ser un número entero",
            "codigo": "FORMATO_ENTERO_INVALIDO",
            "campo": campo
        })
    
    if valor_int < 0:
        raise ValidationError({
            "error": f"El campo {campo} no puede ser negativo",
            "codigo": "VALOR_NEGATIVO",
            "campo": campo
        })
    
    return valor_int


def crear_o_actualizar_plan_venta(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea o actualiza un plan de venta (operación UPSERT).
    
    Si existe un plan para (vendedor_id, periodo), lo actualiza.
    Si no existe, crea uno nuevo.
    
    Args:
        payload: Diccionario con datos del plan:
            - nombre_plan (str): Nombre del plan
            - gerente_id (str): ID del gerente comercial
            - vendedor_id (str): ID del vendedor
            - periodo (str): Periodo YYYY-MM
            - meta_ingresos (decimal): Objetivo de ingresos
            - meta_visitas (int): Objetivo de visitas
            - meta_clientes_nuevos (int): Objetivo de clientes nuevos
            - estado (str, opcional): Estado del plan (default: "activo")
    
    Returns:
        Dict con el plan creado/actualizado
        
    Raises:
        ValidationError: Si hay errores de validación
        NotFoundError: Si el vendedor no existe
        ConflictError: Si hay conflicto de concurrencia
    """
    # Validar campos obligatorios
    require(payload, [
        "nombre_plan",
        "gerente_id", 
        "vendedor_id", 
        "periodo"
    ])
    
    # Extraer y validar datos
    nombre_plan = payload.get("nombre_plan", "").strip()
    gerente_id = payload.get("gerente_id", "").strip()
    vendedor_id = payload.get("vendedor_id", "").strip()
    periodo = payload.get("periodo", "").strip()
    
    # Validar nombre del plan
    if not nombre_plan or len(nombre_plan) < 3:
        raise ValidationError({
            "error": "El nombre del plan debe tener al menos 3 caracteres",
            "codigo": "NOMBRE_PLAN_INVALIDO",
            "campo": "nombre_plan"
        })
    
    if len(nombre_plan) > 200:
        raise ValidationError({
            "error": "El nombre del plan no puede exceder 200 caracteres",
            "codigo": "NOMBRE_PLAN_MUY_LARGO",
            "campo": "nombre_plan"
        })
    
    # Validar formato de periodo
    validar_periodo(periodo)
    
    # Validar que el vendedor existe
    vendedor = db.session.query(Vendedor).filter_by(id=vendedor_id).first()
    if not vendedor:
        raise NotFoundError({
            "error": "Vendedor no encontrado",
            "codigo": "VENDEDOR_NO_ENCONTRADO"
        })
    
    # Validar objetivos/metas
    meta_ingresos = validar_decimal_no_negativo(
        payload.get("meta_ingresos"), 
        "meta_ingresos"
    )
    meta_visitas = validar_entero_no_negativo(
        payload.get("meta_visitas"), 
        "meta_visitas"
    )
    meta_clientes_nuevos = validar_entero_no_negativo(
        payload.get("meta_clientes_nuevos"), 
        "meta_clientes_nuevos"
    )
    
    # Obtener estado (default: activo)
    estado = payload.get("estado", "activo").strip().lower()
    if estado not in ["activo", "inactivo", "completado"]:
        estado = "activo"
    
    # Buscar si ya existe un plan para este vendedor y periodo
    plan_existente = db.session.query(PlanVenta).filter_by(
        vendedor_id=vendedor_id,
        periodo=periodo
    ).first()
    
    try:
        if plan_existente:
            # ACTUALIZAR plan existente
            plan_existente.nombre_plan = nombre_plan
            plan_existente.gerente_id = gerente_id
            plan_existente.meta_ingresos = meta_ingresos
            plan_existente.meta_visitas = meta_visitas
            plan_existente.meta_clientes_nuevos = meta_clientes_nuevos
            plan_existente.estado = estado
            
            db.session.commit()
            
            return {
                **plan_existente.to_dict(),
                "mensaje": "Plan de venta actualizado exitosamente",
                "operacion": "actualizar"
            }
        else:
            # CREAR nuevo plan
            nuevo_plan = PlanVenta(
                id=str(uuid4()),
                nombre_plan=nombre_plan,
                gerente_id=gerente_id,
                vendedor_id=vendedor_id,
                periodo=periodo,
                meta_ingresos=meta_ingresos,
                meta_visitas=meta_visitas,
                meta_clientes_nuevos=meta_clientes_nuevos,
                estado=estado
            )
            
            db.session.add(nuevo_plan)
            db.session.commit()
            
            return {
                **nuevo_plan.to_dict(),
                "mensaje": "Plan de venta creado exitosamente",
                "operacion": "crear"
            }
            
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # Verificar si es error de unicidad
        if 'uq_planes_venta_vendedor_periodo' in error_msg or 'UNIQUE constraint' in error_msg:
            raise ConflictError({
                "error": "Ya existe un plan para ese vendedor y periodo",
                "codigo": "PLAN_DUPLICADO"
            })
        
        # Verificar si es error de FK (vendedor no existe)
        if 'FOREIGN KEY' in error_msg or 'foreign key' in error_msg.lower():
            raise NotFoundError({
                "error": "Vendedor no encontrado",
                "codigo": "VENDEDOR_NO_ENCONTRADO"
            })
        
        raise ConflictError({
            "error": "Error al guardar el plan de venta",
            "codigo": "ERROR_GUARDADO",
            "detalle": error_msg
        })
    except Exception as e:
        db.session.rollback()
        raise ValidationError({
            "error": "Error inesperado al procesar el plan de venta",
            "codigo": "ERROR_INESPERADO",
            "detalle": str(e)
        })


def obtener_plan_venta(plan_id: str) -> Dict[str, Any]:
    """
    Obtiene un plan de venta por su ID.
    
    Args:
        plan_id: ID del plan
        
    Returns:
        Dict con los datos del plan
        
    Raises:
        NotFoundError: Si el plan no existe
    """
    plan = db.session.query(PlanVenta).filter_by(id=plan_id).first()
    
    if not plan:
        raise NotFoundError({
            "error": f"Plan de venta con ID {plan_id} no encontrado",
            "codigo": "PLAN_NO_ENCONTRADO"
        })
    
    return plan.to_dict()


def listar_planes_venta(
    vendedor_id: str = None,
    periodo: str = None,
    estado: str = None,
    page: int = 1,
    size: int = 10
) -> Dict[str, Any]:
    """
    Lista planes de venta con filtros opcionales.
    
    KAN-87: Lista todos los planes con información del vendedor asociado.
    
    Args:
        vendedor_id: Filtrar por vendedor
        periodo: Filtrar por periodo
        estado: Filtrar por estado
        page: Página actual
        size: Tamaño de página
        
    Returns:
        Dict con lista paginada de planes incluyendo información del vendedor
    """
    # Query con join para obtener información del vendedor
    query = db.session.query(PlanVenta).join(
        Vendedor, 
        PlanVenta.vendedor_id == Vendedor.id
    )
    
    # Aplicar filtros
    if vendedor_id:
        query = query.filter(PlanVenta.vendedor_id == vendedor_id)
    
    if periodo:
        query = query.filter(PlanVenta.periodo == periodo)
    
    if estado:
        query = query.filter(PlanVenta.estado == estado)
    
    # Ordenar por fecha de creación descendente
    query = query.order_by(PlanVenta.fecha_creacion.desc())
    
    # Paginación
    total = query.count()
    planes = query.offset((page - 1) * size).limit(size).all()
    
    # Construir respuesta con información del vendedor
    items = []
    for plan in planes:
        plan_dict = plan.to_dict()
        
        # Agregar información del vendedor
        if plan.vendedor:
            plan_dict["vendedor"] = {
                "id": plan.vendedor.id,
                "nombre": plan.vendedor.nombre,
                "apellidos": plan.vendedor.apellidos,
                "correo": plan.vendedor.correo,
                "zona": plan.vendedor.zona
            }
            # Nombre completo del vendedor para la tabla
            plan_dict["vendedor_nombre_completo"] = f"{plan.vendedor.nombre} {plan.vendedor.apellidos}"
        
        items.append(plan_dict)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }
