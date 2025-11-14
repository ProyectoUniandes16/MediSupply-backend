from src.models.camion import Camion
from src.models.tipo_camion import TipoCamion
from src.models.bodega import Bodega
from src import db


class CamionServiceError(Exception):
    """Excepción personalizada para errores del servicio de camiones"""
    def __init__(self, message, status_code=400):
        self.message = {'error': message}
        self.status_code = status_code
        super().__init__(self.message)


def crear_camion(data):
    """
    Crea un nuevo camión
    
    Args:
        data (dict): Datos del camión
        
    Returns:
        dict: Camión creado
        
    Raises:
        CamionServiceError: Si hay un error en la creación
    """
    try:
        if not data:
            raise CamionServiceError('No se proporcionaron datos', 400)
        
        # Validar campos requeridos
        campos_requeridos = ['placa', 'capacidad_kg', 'capacidad_m3', 'bodega_id', 'tipo_camion_id']
        campos_faltantes = [campo for campo in campos_requeridos if campo not in data]
        
        if campos_faltantes:
            raise CamionServiceError(f'Campos faltantes: {", ".join(campos_faltantes)}', 400)
        
        # Verificar que la bodega existe
        bodega = Bodega.query.get(data['bodega_id'])
        if not bodega:
            raise CamionServiceError('La bodega especificada no existe', 404)
        
        # Verificar que el tipo de camión existe
        tipo_camion = TipoCamion.query.get(data['tipo_camion_id'])
        if not tipo_camion:
            raise CamionServiceError('El tipo de camión especificado no existe', 404)
        
        # Verificar que la placa no esté duplicada
        camion_existente = Camion.query.filter_by(placa=data['placa']).first()
        if camion_existente:
            raise CamionServiceError('Ya existe un camión con esa placa', 400)
        
        # Validar capacidades
        if data['capacidad_kg'] <= 0 or data['capacidad_m3'] <= 0:
            raise CamionServiceError('Las capacidades deben ser mayores a 0', 400)
        
        # Crear el camión
        camion = Camion(
            placa=data['placa'],
            capacidad_kg=data['capacidad_kg'],
            capacidad_m3=data['capacidad_m3'],
            bodega_id=data['bodega_id'],
            tipo_camion_id=data['tipo_camion_id'],
            estado=data.get('estado', 'disponible')
        )
        
        db.session.add(camion)
        db.session.commit()
        
        return camion.to_dict_with_tipo()
        
    except CamionServiceError:
        raise
    except Exception as e:
        db.session.rollback()
        raise CamionServiceError(f'Error al crear el camión: {str(e)}', 500)


def listar_camiones():
    """
    Lista todos los camiones
    
    Returns:
        dict: Lista de camiones
    """
    try:
        camiones = Camion.query.all()
        return {
            'data': [camion.to_dict_with_tipo() for camion in camiones],
            'total': len(camiones)
        }
    except Exception as e:
        raise CamionServiceError(f'Error al listar camiones: {str(e)}', 500)


def obtener_camion(camion_id):
    """
    Obtiene un camión por ID
    
    Args:
        camion_id (str): ID del camión
        
    Returns:
        dict: Camión encontrado
        
    Raises:
        CamionServiceError: Si el camión no existe
    """
    try:
        camion = Camion.query.get(camion_id)
        if not camion:
            raise CamionServiceError('Camión no encontrado', 404)
        
        return camion.to_dict_with_tipo()
        
    except CamionServiceError:
        raise
    except Exception as e:
        raise CamionServiceError(f'Error al obtener el camión: {str(e)}', 500)


def listar_camiones_por_bodega(bodega_id):
    """
    Lista todos los camiones de una bodega específica
    
    Args:
        bodega_id (str): ID de la bodega
        
    Returns:
        dict: Lista de camiones de la bodega
        
    Raises:
        CamionServiceError: Si la bodega no existe
    """
    try:
        # Verificar que la bodega existe
        bodega = Bodega.query.get(bodega_id)
        if not bodega:
            raise CamionServiceError('Bodega no encontrada', 404)
        
        camiones = Camion.query.filter_by(bodega_id=bodega_id).all()
        
        return {
            'bodega_id': bodega_id,
            'bodega_nombre': bodega.nombre,
            'camiones': [camion.to_dict_with_tipo() for camion in camiones],
            'total': len(camiones)
        }
        
    except CamionServiceError:
        raise
    except Exception as e:
        raise CamionServiceError(f'Error al listar camiones por bodega: {str(e)}', 500)


def actualizar_estado_camion(camion_id, nuevo_estado):
    """
    Actualiza el estado de un camión
    
    Args:
        camion_id (str): ID del camión
        nuevo_estado (str): Nuevo estado (disponible, en_ruta, mantenimiento)
        
    Returns:
        dict: Camión actualizado
        
    Raises:
        CamionServiceError: Si hay un error en la actualización
    """
    try:
        estados_validos = ['disponible', 'en_ruta', 'mantenimiento']
        
        if nuevo_estado not in estados_validos:
            raise CamionServiceError(
                f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}', 
                400
            )
        
        camion = Camion.query.get(camion_id)
        if not camion:
            raise CamionServiceError('Camión no encontrado', 404)
        
        camion.estado = nuevo_estado
        db.session.commit()
        
        return camion.to_dict_with_tipo()
        
    except CamionServiceError:
        raise
    except Exception as e:
        db.session.rollback()
        raise CamionServiceError(f'Error al actualizar el estado del camión: {str(e)}', 500)
