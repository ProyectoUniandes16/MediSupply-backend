import os
import requests
import json
from flask import current_app, jsonify
from src.config.config import Config as config

class ProductoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de productos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_producto_externo(datos_producto, files, user_id):
    """
    Lógica de negocio para crear un producto a través del microservicio externo.
    Ahora incluye creación automática de inventario.

    Args:
        datos_producto (dict): Datos del producto a crear.
        user_id (str): ID del usuario que realiza la creación.
        files (list): Archivos asociados al producto.
    Returns:
        dict: Los datos del producto creado junto con el inventario creado.

    Raises:
        ProductoServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_producto:
        raise ProductoServiceError({
            'error': 'No se proporcionaron datos',
            'codigo': 'DATOS_VACIOS'
        }, 400)

    # --- Validación de datos de entrada ---
    required_fields = [
        'nombre', 
        'codigo_sku', 
        'categoria', 
        'precio_unitario', 
        'condiciones_almacenamiento', 
        'fecha_vencimiento', 
        'proveedor_id',
        'ubicacion',  # NUEVO: requerido para inventario
        'cantidad_inicial'  # NUEVO: requerido para inventario
        ]
    missing_fields = [field for field in required_fields if not datos_producto.get(field)]
    if missing_fields:
        raise ProductoServiceError({
            'error': f"Campos faltantes: {', '.join(missing_fields)}",
            'codigo': 'CAMPOS_FALTANTES'
            },
              400)
    
    # Validar que cantidad_inicial sea un número válido
    try:
        cantidad_inicial = int(datos_producto.get('cantidad_inicial'))
        if cantidad_inicial < 0:
            raise ValueError("La cantidad inicial no puede ser negativa")
    except (ValueError, TypeError) as e:
        raise ProductoServiceError({
            'error': f'La cantidad_inicial debe ser un número entero válido no negativo',
            'codigo': 'CANTIDAD_INVALIDA'
        }, 400)
    
    # Extraer campos de inventario antes de crear el producto
    ubicacion = datos_producto.get('ubicacion')
    
    data = datos_producto.copy()
    data['usuario_registro'] = user_id
    # Usar cantidad_inicial como cantidad_disponible para el producto
    data['cantidad_disponible'] = cantidad_inicial

    # Remover campos de inventario del payload de producto
    data.pop('ubicacion', None)
    data.pop('cantidad_inicial', None)

    _files = {}
    if 'certificacion' in files:
        file = files['certificacion']
        _files['certificacion'] = (file.filename, file.stream, file.mimetype)
    else:
        raise ProductoServiceError({'error': 'No se proporcionaron archivos de certificación', 'codigo': 'ARCHIVOS_FALTANTES'}, 400)

    # --- Fin de la validación ---

    # PASO 1: Crear el producto
    url_producto = config.PRODUCTO_URL + '/api/productos'
    response = requests.post(
        url_producto,
        data=data,
        files=_files
    )
    if (response.status_code != 201):
        print(f'SERVICE - Error en el microservicio de productos: {response.text}')
        try:
            error_data = response.json()
        except Exception:
            error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
        raise ProductoServiceError(error_data, response.status_code)
    
    datos_respuesta = response.json()
    
    # El microservicio devuelve: {"mensaje": "...", "producto": {...}}
    producto_creado = datos_respuesta.get('producto', datos_respuesta)
    producto_id = producto_creado.get('id')
    
    if not producto_id:
        current_app.logger.error(f"Respuesta del microservicio sin ID: {datos_respuesta}")
        raise ProductoServiceError({
            'error': 'El producto fue creado pero no se obtuvo su ID',
            'codigo': 'PRODUCTO_SIN_ID'
        }, 500)
    
    # PASO 2: Crear el inventario usando InventariosService
    try:
        from src.services.inventarios_service import InventariosService
        
        inventario_data = {
            'productoId': producto_id,  # camelCase como espera el microservicio
            'cantidad': cantidad_inicial,
            'ubicacion': ubicacion,
            'usuario': user_id  # 'usuario' en lugar de 'usuario_creacion'
        }
        
        inventario_creado = InventariosService.crear_inventario(inventario_data)
        
        # Retornar ambos: producto e inventario
        return {
            'producto': producto_creado,
            'inventario': inventario_creado
        }
        
    except Exception as e:
        # Si falla la creación del inventario, loguear el error
        # El producto ya fue creado, así que no podemos hacer rollback
        # El usuario podría crear el inventario manualmente después
        current_app.logger.error(f"❌ Error creando inventario para producto {producto_id}: {str(e)}")
        raise ProductoServiceError({
            'error': f'El producto fue creado exitosamente, pero falló la creación del inventario: {str(e)}',
            'codigo': 'ERROR_INVENTARIO',
            'producto_id': producto_id
        }, 500)
        

def procesar_producto_batch(file_storage, user_id):
    """
    Procesa un archivo CSV con productos, valida cada fila según las mismas reglas
    que crear_producto_externo y retorna un resumen con errores por fila.

    Args:
        file_storage: objeto FileStorage de Flask (archivo CSV).
        user_id: id del usuario que ejecuta la carga.

    Returns:
        dict: resumen con conteos y detalles de errores.
    """
    import csv
    import io
    from datetime import datetime

    if not file_storage:
        raise ProductoServiceError({'error': 'No se proporcionó archivo'}, 400)

    # leer CSV: leer bytes y parsear desde StringIO para no cerrar el stream original
    try:
        # leer todo el contenido en bytes
        file_storage.stream.seek(0)
        file_bytes = file_storage.stream.read()
        # permitir que sea bytes o str
        if isinstance(file_bytes, str):
            text = file_bytes
        else:
            text = file_bytes.decode('utf-8')

        stream = io.StringIO(text)
        reader = csv.DictReader(stream)
    except Exception as e:
        current_app.logger.error(f"Error leyendo CSV: {str(e)}")
        raise ProductoServiceError({'error': 'Error leyendo el archivo CSV'}, 400)

    # Alinear campos requeridos con la validación de crear_producto_externo
    required_fields = [
        'nombre',
        'codigo_sku',
        'categoria',
        'precio_unitario',
        'condiciones_almacenamiento',
        'fecha_vencimiento',
        'proveedor_id'
    ]

    total = 0
    errors = []
    successful = 0
    skus_seen = set()
    valid_rows = []

    def validate_row(idx, row):
        row_errors = []
        missing = [f for f in required_fields if not (row.get(f) and str(row.get(f)).strip())]
        if missing:
            row_errors.append(f"Campos faltantes: {', '.join(missing)}")

        sku = (row.get('codigo_sku') or '').strip()
        if sku:
            if sku in skus_seen:
                row_errors.append('SKU duplicado en archivo')
            else:
                skus_seen.add(sku)

        precio = (row.get('precio_unitario') or '').strip()
        if precio:
            try:
                float(precio)
            except Exception:
                row_errors.append('Precio inválido')

        fecha = (row.get('fecha_vencimiento') or '').strip()
        def try_parse_date(date_str):
            """Intentar parsear la fecha en varios formatos comunes."""
            if not date_str:
                return None
            # intentar ISO primero
            try:
                return datetime.fromisoformat(date_str)
            except Exception:
                pass
            # intentar DD/MM/YYYY y DD-MM-YYYY
            for fmt in ('%d/%m/%Y', '%d-%m-%Y'):
                try:
                    return datetime.strptime(date_str, fmt)
                except Exception:
                    continue
            return None

        if fecha:
            if not try_parse_date(fecha):
                row_errors.append('Fecha inválida')

        # validar fecha de certificación si está presente
        fecha_cert = (row.get('fecha_vencimiento_cert') or '').strip()
        if fecha_cert:
            if not try_parse_date(fecha_cert):
                row_errors.append('Fecha de certificación inválida')

        return row_errors

    for idx, row in enumerate(reader, start=1):
        total += 1
        row_errors = validate_row(idx, row)
        if row_errors:
            errors.append({'fila': idx, 'errors': row_errors, 'row': row})
        else:
            successful += 1
            # normalize row: strip values
            normalized = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            valid_rows.append(normalized)

    # restaurar el stream original para que pueda enviarse posteriormente
    try:
        # reasignar un nuevo BytesIO con los mismos bytes
        file_storage.stream = io.BytesIO(file_bytes if not isinstance(file_bytes, str) else text.encode('utf-8'))
    except Exception:
        # si no es posible restaurar, continuar sin fallo; quien llame debe manejarlo
        current_app.logger.warning('No fue posible restaurar el stream del archivo después de leerlo')

    result = {
        'total': total,
        'successful': successful,
        'failed': len(errors),
        'errors': errors,
        'valid_rows': valid_rows
    }
    return result


def enviar_batch_productos(file_storage, user_id):
    """
    Envía el archivo CSV original al microservicio de productos como multipart/form-data.
    Retorna la respuesta del backend o lanza ProductoServiceError en caso de fallo.
    """
    if not file_storage:
        raise ProductoServiceError({'error': 'No hay archivo para enviar'}, 400)

    url = config.PRODUCTO_URL + '/api/productos/importar-csv'
    headers = {}
    token = os.environ.get('PRODUCTOS_SERVICE_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    # prepare file tuple: (filename, stream, content_type)
    content_type = 'text/csv'
    files = {'archivo': (file_storage.filename, file_storage.stream, content_type)}
    try:
        resp = requests.post(url, files=files, headers=headers, timeout=120)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de red al enviar archivo al servicio de productos: {str(e)}")
        raise ProductoServiceError({'error': 'Error de red al enviar archivo al servicio de productos', 'codigo': 'ERROR_ENVIO_RED', 'detail': str(e)}, 502)

    # si el backend responde con error, extraer detalle (json o texto) y propagarlo
    if resp.status_code >= 400:
        body = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        current_app.logger.error(f"Servicio productos respondió {resp.status_code}: {body}")
        # lanzar error con el detalle y el status real del backend
        raise ProductoServiceError({'error': 'Error desde microservicio de productos', 'detail': body, 'codigo': 'ERROR_BACKEND'}, resp.status_code)

    # éxito
    try:
        return resp.json()
    except Exception:
        return {'status_code': resp.status_code}


def procesar_y_enviar_producto_batch(file_storage, user_id):
    """Procesa el CSV, valida las filas y si hay válidas, envía el archivo al microservicio.

    Retorna un dict con estructura uniforme:
      - ok: True/False
      - status: HTTP status code
      - payload: resumen (si ok True) o mensaje de error/string (si ok False)
    """
    resumen = procesar_producto_batch(file_storage, user_id)

    # Si hay productos válidos, enviar el archivo original
    if resumen.get('successful', 0) > 0:
        try:
            # rewind si es posible
            try:
                file_storage.stream.seek(0)
            except Exception:
                pass
            envio_result = enviar_batch_productos(file_storage, user_id)
            resumen['envio'] = envio_result
            return {'ok': True, 'status': 200, 'payload': resumen}
        except ProductoServiceError as e:
            # Propagar error del servicio como fallo 502 o el status que venga
            return {'ok': False, 'status': e.status_code or 502, 'payload': e.message}
    else:
        # Extraer nombres inválidos
        invalid_names = []
        for err in resumen.get('errors', []):
            row = err.get('row') if isinstance(err, dict) else None
            if isinstance(row, dict):
                name = row.get('nombre') or row.get('name') or row.get('nombre_producto')
                if name:
                    invalid_names.append(name)

        # Construir mensaje de error en un string (detalles JSON incluidos)
        detalles_json = json.dumps(resumen.get('errors', []), ensure_ascii=False)
        mensaje = (
            "Hubo un error en la validación de los productos, no se enviaron productos válidos al microservicio de productos. "
            f"Nombres inválidos: {invalid_names}. Detalles: {detalles_json}"
        )
        return {'ok': False, 'status': 400, 'payload': mensaje}

def consultar_productos_externo(params=None):
    """
    Consulta productos desde el microservicio externo.

    Args:
        params (dict, optional): Parámetros de consulta.

    Returns:
        dict: Datos de los productos consultados.

    Raises:
        ProductoServiceError: Si ocurre un error de conexión o del microservicio.
    """
    url_producto = config.PRODUCTO_URL + '/api/productos/'

    try:
        response = requests.get(
            url_producto,
            params=params
        )

        # raise_for_status normalmente lanzaría HTTPError para 4xx/5xx.
        # Si eso ocurre será capturado por la excepción de requests y convertido
        # en un ProductoServiceError con código de conexión. Si por alguna razón
        # raise_for_status no lanza, comprobamos el status y levantamos
        # ProductoServiceError con el body y status del backend.
        response.raise_for_status()
        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            raise ProductoServiceError(response.json(), response.status_code)
        return response.json()
    except ProductoServiceError:
        # Si ya estamos lanzando un ProductoServiceError (por ejemplo porque el
        # backend devolvió un body con detalles) lo re-lanzamos tal cual para
        # que el caller pueda manejarlo (no lo convertimos en ERROR_CONEXION).
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        # Capturar cualquier otro error inesperado y exponer un error de conexión genérico.
        current_app.logger.error(f"Error inesperado consultando microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)


def obtener_detalle_producto_externo(producto_id):
    """
    Obtiene el detalle completo de un producto por ID desde el microservicio.

    Args:
        producto_id (int): ID del producto a consultar.

    Returns:
        dict: Detalle completo del producto incluyendo stock y certificaciones.

    Raises:
        ProductoServiceError: Si el producto no existe o hay error de conexión.
    """
    url_producto = f"{config.PRODUCTO_URL}/api/productos/{producto_id}"

    try:
        response = requests.get(url_producto)

        if response.status_code == 404:
            current_app.logger.warning(f"Producto {producto_id} no encontrado")
            raise ProductoServiceError({
                'error': f'Producto con ID {producto_id} no encontrado',
                'codigo': 'PRODUCTO_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle de producto: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al obtener detalle del producto',
            'codigo': 'ERROR_INESPERADO'
        }, 500)


def obtener_producto_por_sku_externo(sku):
    """
    Obtiene el detalle de un producto por código SKU desde el microservicio.

    Args:
        sku (str): Código SKU del producto.

    Returns:
        dict: Detalle completo del producto.

    Raises:
        ProductoServiceError: Si el SKU no existe o hay error de conexión.
    """
    if not sku or not sku.strip():
        raise ProductoServiceError({
            'error': 'El código SKU es requerido',
            'codigo': 'SKU_REQUERIDO'
        }, 400)

    url_producto = f"{config.PRODUCTO_URL}/api/productos/sku/{sku}"

    try:
        response = requests.get(url_producto)

        if response.status_code == 404:
            current_app.logger.warning(f"Producto con SKU {sku} no encontrado")
            raise ProductoServiceError({
                'error': f'Producto con SKU {sku} no encontrado',
                'codigo': 'PRODUCTO_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo producto por SKU: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al obtener producto por SKU',
            'codigo': 'ERROR_INESPERADO'
        }, 500)


def descargar_certificacion_producto_externo(producto_id):
    """
    Descarga la certificación de un producto desde el microservicio.

    Args:
        producto_id (int): ID del producto.

    Returns:
        tuple: (file_content, filename, mimetype) para enviar con send_file.

    Raises:
        ProductoServiceError: Si no hay certificación disponible o hay error.
    """
    url_certificacion = f"{config.PRODUCTO_URL}/api/productos/{producto_id}/certificacion/descargar"

    try:
        response = requests.get(url_certificacion, stream=True)

        if response.status_code == 404:
            current_app.logger.warning(f"Certificación no encontrada para producto {producto_id}")
            raise ProductoServiceError({
                'error': 'No hay certificación disponible para este producto',
                'codigo': 'CERTIFICACION_NO_ENCONTRADA'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error al descargar certificación: {response.status_code}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': 'Error al descargar certificación', 'codigo': 'ERROR_DESCARGA'}
            raise ProductoServiceError(error_data, response.status_code)

        # Extraer información del archivo desde headers
        content_disposition = response.headers.get('Content-Disposition', '')
        filename = 'certificacion.pdf'  # default
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')

        mimetype = response.headers.get('Content-Type', 'application/pdf')
        file_content = response.content

        return file_content, filename, mimetype

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión al descargar certificación: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado descargando certificación: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al descargar certificación',
            'codigo': 'ERROR_INESPERADO'
        }, 500)


def obtener_status_importacion_externo(job_id, include_errors=False):
    """
    Consulta el estado de un job de importación en el microservicio de productos.

    Args:
        job_id (str): ID del job de importación.
        include_errors (bool): Si incluir detalles de errores.

    Returns:
        dict: Estado del job.

    Raises:
        ProductoServiceError: Si el job no existe o hay error de conexión.
    """
    url_status = f"{config.PRODUCTO_URL}/api/productos/importar-csv/status/{job_id}"
    params = {'include_errors': 'true' if include_errors else 'false'}

    try:
        response = requests.get(url_status, params=params)

        if response.status_code == 404:
            current_app.logger.warning(f"Job de importación {job_id} no encontrado")
            raise ProductoServiceError({
                'error': f'Job de importación {job_id} no encontrado',
                'codigo': 'JOB_NO_ENCONTRADO'
            }, 404)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo status de importación: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al obtener status de importación',
            'codigo': 'ERROR_INESPERADO'
        }, 500)


def listar_jobs_importacion_externo(params=None):
    """
    Lista los jobs de importación desde el microservicio de productos.

    Args:
        params (dict, optional): Parámetros de consulta (usuario, estado, limit, offset).

    Returns:
        dict: Lista de jobs y metadatos de paginación.

    Raises:
        ProductoServiceError: Si hay error de conexión o del microservicio.
    """
    url_jobs = f"{config.PRODUCTO_URL}/api/productos/importar-csv/jobs"

    try:
        response = requests.get(url_jobs, params=params)

        if response.status_code != 200:
            current_app.logger.error(f"Error del microservicio de productos: {response.text}")
            try:
                error_data = response.json()
            except Exception:
                error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
            raise ProductoServiceError(error_data, response.status_code)

        return response.json()

    except ProductoServiceError:
        raise
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de productos: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error de conexión con el microservicio de productos',
            'codigo': 'ERROR_CONEXION'
        }, 503)
    except Exception as e:
        current_app.logger.error(f"Error inesperado listando jobs de importación: {str(e)}")
        raise ProductoServiceError({
            'error': 'Error interno al listar jobs de importación',
            'codigo': 'ERROR_INESPERADO'
        }, 500)