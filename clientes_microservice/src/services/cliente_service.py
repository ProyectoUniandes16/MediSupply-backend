import unicodedata
from flask import current_app
from src.models.cliente import Cliente, db

class ClienteServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de clientes."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def register_cliente(data):
    """
    Lógica de negocio para registrar un nuevo cliente.
    """
    if data is None:
        raise ClienteServiceError({'error': 'No se proporcionaron datos'}, 400)

    required_fields = ['nombre', 'tipo', 'zona', 'nombre_contacto', 'cargo_contacto', 'correo_contacto', 'telefono_contacto', 'nit', 'correo_empresa']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ClienteServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    email = data['correo_empresa'].lower().strip()
    if '@' not in email or '.' not in email:
        raise ClienteServiceError({'error': 'Formato de email inválido', 'codigo': 'FORMATO_EMAIL_INVALIDO'}, 400)
    
    email = data['correo_contacto'].lower().strip()
    if '@' not in email or '.' not in email:
        raise ClienteServiceError({'error': 'Formato de email inválido', 'codigo': 'FORMATO_EMAIL_INVALIDO'}, 400)
    if Cliente.query.filter_by(correo_contacto=email).first():
        raise ClienteServiceError({'error': f'Un cliente ya existe con el email {email}', 'codigo': 'CONTACTO_YA_EXISTE'}, 409)
        
    if len(data['telefono_contacto']) < 7:
        raise ClienteServiceError({'error': 'El teléfono de contacto es demasiado corto', 'codigo': 'TELEFONO_CORTO'}, 400)
    if data['telefono_contacto'][0] not in '0123456789':
        raise ClienteServiceError({'error': 'El teléfono de contacto deben ser números', 'codigo': 'TELEFONO_NO_NUMERICO'}, 400)
    
    nit = data['nit'].strip()
    if nit and len(nit) < 9 or len(nit) > 10:
        raise ClienteServiceError({'error': 'El NIT es demasiado corto o largo', 'codigo': 'NIT_CORTO_LARGO'}, 400)
    if Cliente.query.filter_by(nit=nit).first():
        raise ClienteServiceError({'error': f'El cliente con el NIT {nit} ya existe', 'codigo': 'CLIENTE_YA_EXISTE'}, 409)
    print(f"Creando cliente... {data}")

    # Asegurar que `zona` es un string y normalizar (sin mayúsculas ni acentos)
    zona_raw = data.get('zona')
    zona = str(zona_raw).strip() if zona_raw is not None else ''
    zona_norm = _normalize(zona)

    # Mapeo de zonas a rangos (lat_min, lat_max), (lon_min, lon_max)
    zonas_ranges = {
        'bogota': ((4.60, 4.73), (-74.12, -74.04)),
        'ciudad de mexico': ((19.27, 19.59), (-99.29, -98.97)),
        'lima': ((-12.20, -11.70), (-77.10, -76.80)),
        'quito': ((-0.30, -0.05), (-78.60, -78.35)),
    }

    if zona_norm in zonas_ranges:
        (lat_min, lat_max), (lon_min, lon_max) = zonas_ranges[zona_norm]
        lat = _ubicacion_random(lat_min, lat_max)
        lon = _ubicacion_random(lon_min, lon_max)
        data['ubicacion'] = f"{lat},{lon}"
    else:
        # Usar cadena vacía en vez de None para evitar .strip() sobre None más abajo
        data['ubicacion'] = ''

    try:
        cliente = Cliente(
            nombre=data['nombre'].strip(),
            tipo=data['tipo'].strip(),
            zona=data['zona'].strip(),
            nombre_contacto=data['nombre_contacto'].strip(),
            cargo_contacto=data['cargo_contacto'].strip(),
            correo_contacto=data['correo_contacto'].strip(),
            correo_empresa=data.get('correo_empresa').strip(),
            telefono_contacto=data['telefono_contacto'].strip(),
            direccion=data.get('direccion', '').strip(),
            ubicacion=(data.get('ubicacion') or '').strip(),
            nit=nit
        )
        cliente.save()
    except Exception as e:
        error_message = "Error al crear el cliente"
        print(error_message + f": {str(e)}")
        raise ClienteServiceError({'error': error_message, 'codigo': 'ERROR_CREAR_CLIENTE'}, 500)

    return {
        'data': {
            'cliente': cliente.to_dict(),
            'message': 'Cliente creado exitosamente',
        }
    }

def _normalize(s: str) -> str:
    # Normaliza Unicode y elimina diacríticos para comparar sin acentos
    s = s or ''
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in nfkd if not unicodedata.combining(ch)).lower().strip()

def _ubicacion_random(top, down):
    """Genera una ubicación aleatoria (latitud, longitud) dentro de Bogotá."""
    import random
    numero_aleatorio = random.uniform(top, down)
    return numero_aleatorio


def list_clientes(filtros=None):  # -> dict[str, list]:
    """
    Retorna la lista de clientes aplicando filtros combinados.

    Filtros soportados (pasar en el dict `filtros`):
      - ids: filtrar clientes asociados a un vendedor (usa tabla vendedor_clientes)

    Retorna:
        dict: {
            'data': [<cliente_dict>, ...]
        }
    """
    try:
        query = Cliente.query

        ids = filtros.get('ids') if filtros else None
        if ids:
            current_app.logger.info(f"Filtrando por ids: {ids}")
            cliente_ids = ids.split(',')
            current_app.logger.info(f"Cliente ids: {cliente_ids}")
            if cliente_ids:
                query = query.filter(Cliente.id.in_(cliente_ids))

        if filtros.get('correo_empresa'):
            correo = filtros['correo_empresa'].strip().lower()
            print(f"Filtrando por correo_empresa: {correo}")
            query = query.filter(Cliente.correo_empresa.ilike(f"%{correo}%"))

        clientes = query.all()

        return {
            'data': [c.to_dict() for c in clientes]
        }

    except ClienteServiceError:
        # Propagar errores de servicio tal cual
        raise
    except Exception as e:
        print(f"Error al listar clientes: {e}")
        raise ClienteServiceError({'error': 'Error obteniendo lista de clientes', 'codigo': 'ERROR_LISTAR_CLIENTES'}, 500)


def get_cliente_by_id(cliente_id):
    """
    Obtiene un cliente por su ID.
    
    Args:
        cliente_id (int): ID del cliente
        
    Returns:
        dict: Datos del cliente
        
    Raises:
        ClienteServiceError: Si el cliente no existe
    """
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            raise ClienteServiceError({'error': f'Cliente con ID {cliente_id} no encontrado', 'codigo': 'CLIENTE_NO_ENCONTRADO'}, 404)
        
        return {'data': cliente.to_dict()}
        
    except ClienteServiceError:
        raise
    except Exception as e:
        print(f"Error al obtener cliente {cliente_id}: {e}")
        raise ClienteServiceError({'error': 'Error obteniendo cliente', 'codigo': 'ERROR_OBTENER_CLIENTE'}, 500)