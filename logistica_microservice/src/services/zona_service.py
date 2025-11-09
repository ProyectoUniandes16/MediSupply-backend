from flask import current_app
from src.models.zona import Zona, db


class ZonaServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de zonas."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def crear_zona(data):
    """
    Función para crear una nueva zona
    
    Args:
        data (dict): Datos de la zona a crear
        
    Returns:
        dict: Datos de la zona creada
        
    Raises:
        ZonaServiceError: Si hay errores en la creación
    """
    if data is None:
        raise ZonaServiceError({'error': 'No se proporcionaron datos'}, 400)

    required_fields = ['nombre', 'latitud_maxima', 'latitud_minima', 'longitud_maxima', 'longitud_minima']
    missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]
    if missing_fields:
        raise ZonaServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    # Validar que las coordenadas sean números
    try:
        latitud_maxima = float(data['latitud_maxima'])
        latitud_minima = float(data['latitud_minima'])
        longitud_maxima = float(data['longitud_maxima'])
        longitud_minima = float(data['longitud_minima'])
    except (ValueError, TypeError):
        raise ZonaServiceError({'error': 'Las coordenadas deben ser números válidos'}, 400)

    # Validar rangos de coordenadas
    if not (-90 <= latitud_maxima <= 90 and -90 <= latitud_minima <= 90):
        raise ZonaServiceError({'error': 'Las latitudes deben estar entre -90 y 90'}, 400)
    
    if not (-180 <= longitud_maxima <= 180 and -180 <= longitud_minima <= 180):
        raise ZonaServiceError({'error': 'Las longitudes deben estar entre -180 y 180'}, 400)
    
    if latitud_minima >= latitud_maxima:
        raise ZonaServiceError({'error': 'La latitud mínima debe ser menor que la máxima'}, 400)
    
    if longitud_minima >= longitud_maxima:
        raise ZonaServiceError({'error': 'La longitud mínima debe ser menor que la máxima'}, 400)

    # Verificar si ya existe una zona con ese nombre
    zona_existente = Zona.query.filter_by(nombre=data['nombre']).first()
    if zona_existente:
        raise ZonaServiceError({'error': 'Ya existe una zona con ese nombre', 'codigo': 'ZONA_DUPLICADA'}, 400)

    try:
        zona = Zona(
            nombre=data['nombre'],
            latitud_maxima=latitud_maxima,
            latitud_minima=latitud_minima,
            longitud_maxima=longitud_maxima,
            longitud_minima=longitud_minima
        )
        zona.save()
        
        current_app.logger.info(f"Zona creada exitosamente: {zona.id}")
        return zona.to_dict()
    except Exception as e:
        current_app.logger.error(f"Error al guardar la zona: {str(e)}")
        raise ZonaServiceError({'error': 'Error al guardar la zona', 'codigo': 'ERROR_GUARDAR_ZONA'}, 500)


def listar_zonas():
    """
    Lista todas las zonas
    
    Returns:
        dict: Diccionario con la lista de zonas
    """
    try:
        zonas = Zona.query.all()
        return {
            "data": [zona.to_dict() for zona in zonas],
            "total": len(zonas)
        }
    except Exception as e:
        current_app.logger.error(f"Error al listar zonas: {str(e)}")
        raise ZonaServiceError({'error': 'Error al listar zonas', 'codigo': 'ERROR_LISTAR_ZONAS'}, 500)


def obtener_zona(zona_id):
    """
    Obtiene una zona por su ID
    
    Args:
        zona_id (str): ID de la zona
        
    Returns:
        dict: Datos de la zona
        
    Raises:
        ZonaServiceError: Si la zona no existe
    """
    try:
        zona = Zona.query.get(zona_id)
        if not zona:
            raise ZonaServiceError({'error': 'Zona no encontrada', 'codigo': 'ZONA_NO_ENCONTRADA'}, 404)
        
        return zona.to_dict()
    except ZonaServiceError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error al obtener zona: {str(e)}")
        raise ZonaServiceError({'error': 'Error al obtener zona', 'codigo': 'ERROR_OBTENER_ZONA'}, 500)


def listar_zonas_con_bodegas():
    """
    Lista todas las zonas con sus bodegas asociadas
    
    Returns:
        dict: Diccionario con la lista de zonas y sus bodegas
    """
    try:
        zonas = Zona.query.all()
        return {
            "data": [zona.to_dict_with_bodegas() for zona in zonas],
            "total": len(zonas)
        }
    except Exception as e:
        current_app.logger.error(f"Error al listar zonas con bodegas: {str(e)}")
        raise ZonaServiceError({'error': 'Error al listar zonas con bodegas', 'codigo': 'ERROR_LISTAR_ZONAS_BODEGAS'}, 500)
