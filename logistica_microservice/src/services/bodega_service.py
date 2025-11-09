from flask import current_app
from src.models.bodega import Bodega
from src.models.zona import Zona, db


class BodegaServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de bodegas."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def crear_bodega(data):
    """
    Función para crear una nueva bodega y asociarla a una o más zonas
    
    Args:
        data (dict): Datos de la bodega a crear
        
    Returns:
        dict: Datos de la bodega creada
        
    Raises:
        BodegaServiceError: Si hay errores en la creación
    """
    if data is None:
        raise BodegaServiceError({'error': 'No se proporcionaron datos'}, 400)

    required_fields = ['nombre', 'ubicacion', 'zona_id']
    missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]
    if missing_fields:
        raise BodegaServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    # Validar que la zona existe
    zona_id = data['zona_id']
    zona = Zona.query.get(zona_id)
    if not zona:
        raise BodegaServiceError({'error': 'La zona especificada no existe', 'codigo': 'ZONA_NO_ENCONTRADA'}, 404)

    try:
        bodega = Bodega(
            nombre=data['nombre'],
            ubicacion=data['ubicacion']
        )
        bodega.save()
        
        # Asociar la bodega a la zona
        zona.bodegas.append(bodega)
        db.session.commit()
        
        current_app.logger.info(f"Bodega creada exitosamente: {bodega.id}")
        return bodega.to_dict()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al guardar la bodega: {str(e)}")
        raise BodegaServiceError({'error': 'Error al guardar la bodega', 'codigo': 'ERROR_GUARDAR_BODEGA'}, 500)


def listar_bodegas():
    """
    Lista todas las bodegas
    
    Returns:
        dict: Diccionario con la lista de bodegas
    """
    try:
        bodegas = Bodega.query.all()
        return {
            "data": [bodega.to_dict() for bodega in bodegas],
            "total": len(bodegas)
        }
    except Exception as e:
        current_app.logger.error(f"Error al listar bodegas: {str(e)}")
        raise BodegaServiceError({'error': 'Error al listar bodegas', 'codigo': 'ERROR_LISTAR_BODEGAS'}, 500)


def obtener_bodega(bodega_id):
    """
    Obtiene una bodega por su ID
    
    Args:
        bodega_id (str): ID de la bodega
        
    Returns:
        dict: Datos de la bodega
        
    Raises:
        BodegaServiceError: Si la bodega no existe
    """
    try:
        bodega = Bodega.query.get(bodega_id)
        if not bodega:
            raise BodegaServiceError({'error': 'Bodega no encontrada', 'codigo': 'BODEGA_NO_ENCONTRADA'}, 404)
        
        return bodega.to_dict()
    except BodegaServiceError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error al obtener bodega: {str(e)}")
        raise BodegaServiceError({'error': 'Error al obtener bodega', 'codigo': 'ERROR_OBTENER_BODEGA'}, 500)
