from calendar import c
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

    required_fields = ['nombre', 'tipo', 'pais', 'nombre_contacto', 'cargo_contacto', 'correo_contacto', 'telefono_contacto', 'nit', 'correo_empresa']
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
    try:
        cliente = Cliente(
            nombre=data['nombre'].strip(),
            tipo=data['tipo'].strip(),
            pais=data['pais'].strip(),
            nombre_contacto=data['nombre_contacto'].strip(),
            cargo_contacto=data['cargo_contacto'].strip(),
            correo_contacto=data['correo_contacto'].strip(),
            correo_empresa=data.get('correo_empresa').strip(),
            telefono_contacto=data['telefono_contacto'].strip(),
            direccion=data.get('direccion', '').strip(),
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