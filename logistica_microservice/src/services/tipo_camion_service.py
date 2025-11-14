from src.models.tipo_camion import TipoCamion
from src import db


class TipoCamionServiceError(Exception):
    """Excepción personalizada para errores del servicio de tipos de camión"""
    def __init__(self, message, status_code=400):
        self.message = {'error': message}
        self.status_code = status_code
        super().__init__(self.message)


def crear_tipo_camion(data):
    """
    Crea un nuevo tipo de camión
    
    Args:
        data (dict): Datos del tipo de camión
        
    Returns:
        dict: Tipo de camión creado
        
    Raises:
        TipoCamionServiceError: Si hay un error en la creación
    """
    try:
        if not data:
            raise TipoCamionServiceError('No se proporcionaron datos', 400)
        
        # Validar campos requeridos
        if 'nombre' not in data:
            raise TipoCamionServiceError('El campo nombre es requerido', 400)
        
        # Verificar que el nombre no esté duplicado
        tipo_existente = TipoCamion.query.filter_by(nombre=data['nombre']).first()
        if tipo_existente:
            raise TipoCamionServiceError('Ya existe un tipo de camión con ese nombre', 400)
        
        # Crear el tipo de camión
        tipo_camion = TipoCamion(
            nombre=data['nombre'],
            descripcion=data.get('descripcion')
        )
        
        db.session.add(tipo_camion)
        db.session.commit()
        
        return tipo_camion.to_dict()
        
    except TipoCamionServiceError:
        raise
    except Exception as e:
        db.session.rollback()
        raise TipoCamionServiceError(f'Error al crear el tipo de camión: {str(e)}', 500)


def listar_tipos_camion():
    """
    Lista todos los tipos de camión
    
    Returns:
        dict: Lista de tipos de camión
    """
    try:
        tipos = TipoCamion.query.all()
        return {
            'data': [tipo.to_dict() for tipo in tipos],
            'total': len(tipos)
        }
    except Exception as e:
        raise TipoCamionServiceError(f'Error al listar tipos de camión: {str(e)}', 500)


def obtener_tipo_camion(tipo_id):
    """
    Obtiene un tipo de camión por ID
    
    Args:
        tipo_id (str): ID del tipo de camión
        
    Returns:
        dict: Tipo de camión encontrado
        
    Raises:
        TipoCamionServiceError: Si el tipo no existe
    """
    try:
        tipo = TipoCamion.query.get(tipo_id)
        if not tipo:
            raise TipoCamionServiceError('Tipo de camión no encontrado', 404)
        
        return tipo.to_dict()
        
    except TipoCamionServiceError:
        raise
    except Exception as e:
        raise TipoCamionServiceError(f'Error al obtener el tipo de camión: {str(e)}', 500)


def inicializar_tipos_camion():
    """
    Inicializa los tipos de camión predeterminados si no existen
    
    Returns:
        dict: Tipos de camión creados
    """
    try:
        tipos_default = [
            {'nombre': 'Refrigerado', 'descripcion': 'Camión con sistema de refrigeración para productos que requieren temperatura controlada'},
            {'nombre': 'Sin Refrigeración', 'descripcion': 'Camión estándar para productos que no requieren refrigeración'},
            {'nombre': 'Mixto', 'descripcion': 'Camión con compartimentos refrigerados y sin refrigeración'}
        ]
        
        tipos_creados = []
        
        for tipo_data in tipos_default:
            tipo_existente = TipoCamion.query.filter_by(nombre=tipo_data['nombre']).first()
            if not tipo_existente:
                tipo = TipoCamion(
                    nombre=tipo_data['nombre'],
                    descripcion=tipo_data['descripcion']
                )
                db.session.add(tipo)
                tipos_creados.append(tipo_data['nombre'])
        
        if tipos_creados:
            db.session.commit()
        
        return {
            'message': 'Tipos de camión inicializados',
            'tipos_creados': tipos_creados,
            'total': len(tipos_creados)
        }
        
    except Exception as e:
        db.session.rollback()
        raise TipoCamionServiceError(f'Error al inicializar tipos de camión: {str(e)}', 500)
