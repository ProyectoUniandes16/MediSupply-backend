from flask import current_app
from src.models.zona import Zona, db
from src.models.bodega import Bodega
from src.models.camion import Camion
from src.models.tipo_camion import TipoCamion


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


def obtener_zona_detallada(zona_id):
    """
    Obtiene el detalle completo de una zona con sus bodegas y camiones
    
    Args:
        zona_id (str): ID de la zona
        
    Returns:
        dict: Zona con bodegas y sus camiones
        
    Raises:
        ZonaServiceError: Si la zona no existe
    """
    try:
        zona = Zona.query.get(zona_id)
        if not zona:
            raise ZonaServiceError({'error': 'Zona no encontrada', 'codigo': 'ZONA_NO_ENCONTRADA'}, 404)
        
        # Obtener datos de la zona
        zona_data = zona.to_dict()
        
        # Agregar bodegas con sus camiones
        bodegas_con_camiones = []
        for bodega in zona.bodegas:
            bodega_data = bodega.to_dict_with_camiones()
            bodegas_con_camiones.append(bodega_data)
        
        zona_data['bodegas'] = bodegas_con_camiones
        
        return zona_data
        
    except ZonaServiceError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error al obtener zona detallada: {str(e)}")
        raise ZonaServiceError({'error': 'Error al obtener zona detallada', 'codigo': 'ERROR_OBTENER_ZONA_DETALLADA'}, 500)


def inicializar_zonas():
    """
    Inicializa las zonas por defecto con sus bodegas centrales y camiones.
    
    Crea 4 zonas (México DF, Bogotá, Quito, Lima) cada una con:
    - Una bodega central
    - 3 camiones (uno de cada tipo: Refrigerado, Sin Refrigeración, Mixto)
    
    Returns:
        dict: Mensaje de éxito con las zonas creadas
        
    Raises:
        ZonaServiceError: Si hay errores en la inicialización
    """
    try:
        # Definir las zonas con sus datos
        zonas_data = [
            {
                "nombre": "México - Ciudad de México",
                "latitud_minima": 19.27,
                "latitud_maxima": 19.59,
                "longitud_minima": -99.29,
                "longitud_maxima": -98.97,
                "bodega": {
                    "nombre": "Bodega Central CDMX",
                    "ubicacion": "19.4326,-99.1332"  # Centro de Ciudad de México
                }
            },
            {
                "nombre": "Colombia - Bogotá",
                "latitud_minima": 4.6,
                "latitud_maxima": 4.73,
                "longitud_minima": -74.12,
                "longitud_maxima": -74.04,
                "bodega": {
                    "nombre": "Bodega Kennedy",
                    "ubicacion": "4.636767,-74.140675"
                }
            },
            {
                "nombre": "Ecuador - Quito",
                "latitud_minima": -0.3,
                "latitud_maxima": 0.05,
                "longitud_minima": -78.6,
                "longitud_maxima": -78.35,
                "bodega": {
                    "nombre": "Bodega Central Quito",
                    "ubicacion": "-0.1807,-78.4678"  # Centro de Quito
                }
            },
            {
                "nombre": "Perú - Lima",
                "latitud_minima": -12.2,
                "latitud_maxima": -11.7,
                "longitud_minima": -77.1,
                "longitud_maxima": -76.8,
                "bodega": {
                    "nombre": "Bodega Central Lima",
                    "ubicacion": "-12.0464,-77.0428"  # Centro de Lima
                }
            }
        ]
        
        # Obtener los tipos de camión
        tipo_refrigerado = TipoCamion.query.filter_by(nombre="Refrigerado").first()
        tipo_sin_refrigeracion = TipoCamion.query.filter_by(nombre="Sin Refrigeración").first()
        tipo_mixto = TipoCamion.query.filter_by(nombre="Mixto").first()
        
        # Verificar que los tipos de camión existan
        if not all([tipo_refrigerado, tipo_sin_refrigeracion, tipo_mixto]):
            raise ZonaServiceError({
                'error': 'Los tipos de camión no están inicializados. Ejecute primero POST /tipo-camion/inicializar',
                'codigo': 'TIPOS_CAMION_NO_INICIALIZADOS'
            }, 400)
        
        zonas_creadas = []
        bodegas_creadas = []
        camiones_creados = []
        
        for zona_data in zonas_data:
            # Verificar si ya existe la zona
            zona_existente = Zona.query.filter_by(nombre=zona_data["nombre"]).first()
            if zona_existente:
                current_app.logger.info(f"Zona '{zona_data['nombre']}' ya existe, se omite.")
                continue
            
            # Crear la zona
            zona = Zona(
                nombre=zona_data["nombre"],
                latitud_minima=zona_data["latitud_minima"],
                latitud_maxima=zona_data["latitud_maxima"],
                longitud_minima=zona_data["longitud_minima"],
                longitud_maxima=zona_data["longitud_maxima"]
            )
            zona.save()
            zonas_creadas.append(zona.nombre)
            current_app.logger.info(f"Zona creada: {zona.nombre}")
            
            # Crear la bodega central
            bodega = Bodega(
                nombre=zona_data["bodega"]["nombre"],
                ubicacion=zona_data["bodega"]["ubicacion"]
            )
            bodega.zonas.append(zona)
            bodega.save()
            bodegas_creadas.append(bodega.nombre)
            current_app.logger.info(f"Bodega creada: {bodega.nombre}")
            
            # Crear los camiones para esta bodega
            camiones_data = [
                {
                    "placa": f"REF-{zona.nombre[:3].upper()}-001",
                    "tipo": tipo_refrigerado,
                    "capacidad_kg": 5000,
                    "capacidad_m3": 30
                },
                {
                    "placa": f"SIN-{zona.nombre[:3].upper()}-001",
                    "tipo": tipo_sin_refrigeracion,
                    "capacidad_kg": 8000,
                    "capacidad_m3": 40
                },
                {
                    "placa": f"MIX-{zona.nombre[:3].upper()}-001",
                    "tipo": tipo_mixto,
                    "capacidad_kg": 6000,
                    "capacidad_m3": 35
                }
            ]
            
            for camion_data in camiones_data:
                camion = Camion(
                    placa=camion_data["placa"],
                    capacidad_kg=camion_data["capacidad_kg"],
                    capacidad_m3=camion_data["capacidad_m3"],
                    estado="disponible",
                    bodega_id=bodega.id,
                    tipo_camion_id=camion_data["tipo"].id
                )
                db.session.add(camion)
                camiones_creados.append(camion.placa)
                current_app.logger.info(f"Camión creado: {camion.placa}")
        
        # Commit de todos los cambios
        db.session.commit()
        
        if not zonas_creadas:
            return {
                "mensaje": "Todas las zonas ya estaban inicializadas",
                "zonas_existentes": len(zonas_data)
            }
        
        return {
            "mensaje": "Zonas inicializadas exitosamente",
            "zonas_creadas": zonas_creadas,
            "bodegas_creadas": bodegas_creadas,
            "camiones_creados": camiones_creados,
            "total_zonas": len(zonas_creadas),
            "total_bodegas": len(bodegas_creadas),
            "total_camiones": len(camiones_creados)
        }
        
    except ZonaServiceError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error al inicializar zonas: {str(e)}")
        db.session.rollback()
        raise ZonaServiceError({
            'error': 'Error al inicializar zonas',
            'detalle': str(e),
            'codigo': 'ERROR_INICIALIZAR_ZONAS'
        }, 500)
