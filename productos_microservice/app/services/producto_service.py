from app.extensions import db
from app.models.producto import Producto, CertificacionProducto
from app.utils.validators import ProductoValidator, CertificacionValidator
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask import current_app
import os
import uuid


class ConflictError(Exception):
    """Excepción personalizada para conflictos (ej. SKU duplicado)"""
    pass


class ProductoService:
    """Servicio para gestión de productos"""
    
    @staticmethod
    def obtener_detalle_completo(producto_id=None, sku=None):
        """
        Obtiene detalle completo de un producto con toda su información
        Permite búsqueda por ID o SKU
        
        Args:
            producto_id: ID del producto (opcional)
            sku: SKU del producto (opcional)
            
        Returns:
            Diccionario con toda la información del producto
            
        Raises:
            ValueError: Si no se encuentra el producto o no se proporciona ID/SKU
        """
        # Validar que se proporcione al menos un parámetro
        if not producto_id and not sku:
            raise ValueError("Debe proporcionar producto_id o sku")
        
        # Buscar producto con eager loading para evitar N+1 queries
        query = Producto.query.options(db.joinedload(Producto.certificacion))
        
        if producto_id:
            producto = query.get(producto_id)
        else:
            producto = query.filter_by(codigo_sku=sku).first()
        
        if not producto:
            raise ValueError("Producto no encontrado")
        
        # Construir respuesta completa con toda la información
        detalle = {
            "id": producto.id,
            "nombre": producto.nombre,
            "codigo_sku": producto.codigo_sku,
            "categoria": producto.categoria,
            "precio_unitario": float(producto.precio_unitario),
            "condiciones_almacenamiento": producto.condiciones_almacenamiento,
            "fecha_vencimiento": producto.fecha_vencimiento.strftime("%d/%m/%Y"),
            "estado": producto.estado,
            "proveedor_id": producto.proveedor_id,
            
            # Inventario
            "inventario": {
                "cantidad_disponible": producto.cantidad_disponible,
                "tiene_stock": producto.tiene_stock_disponible()
            },
            
            # Certificaciones con estado calculado
            "certificaciones": [],
            
            # Trazabilidad
            "trazabilidad": {
                "fecha_creacion": producto.fecha_registro.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "fecha_actualizacion": producto.fecha_actualizacion.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "usuario_registro": producto.usuario_registro
            }
        }
        
        # Agregar certificación si existe
        if producto.certificacion:
            cert = producto.certificacion
            estado_cert = "Activo" if producto.certificacion_activa() else "Inactivo"
            
            detalle["certificaciones"].append({
                "id": cert.id,
                "tipo_certificacion": cert.tipo_certificacion,
                "nombre_archivo": cert.nombre_archivo,
                "tamaño_archivo": cert.tamaño_archivo,
                "fecha_emision": cert.fecha_subida.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "fecha_vencimiento": cert.fecha_vencimiento_cert.strftime("%d/%m/%Y"),
                "estado": estado_cert,
                "url_descarga": f"/api/productos/{producto.id}/certificacion/descargar"
            })
        
        return detalle
    
    @staticmethod
    def crear_producto(data, archivos_certificacion):
        """
        Crea un nuevo producto con su certificación
        
        Args:
            data: Diccionario con datos del producto
            archivos_certificacion: Lista de archivos de certificación
            
        Returns:
            Producto creado
            
        Raises:
            ValueError: Si los datos son inválidos
            ConflictError: Si el SKU ya existe
        """
        try:
            # 1. FAIL-FAST: Validar campos obligatorios primero
            ProductoValidator.validar_campos_obligatorios(data)
            
            # 2. Validar SKU antes de hacer operaciones costosas
            ProductoValidator.validar_formato_sku(data['codigo_sku'])
            
            # 3. Verificar que el SKU no exista (antes de validar archivos)
            if ProductoService._verificar_sku_existe(data['codigo_sku']):
                raise ConflictError({
                    "error": f"Ya existe un producto registrado con el SKU {data['codigo_sku']}",
                    "codigo": "SKU_DUPLICADO",
                    "sku": data['codigo_sku']
                })
            
            # 4. Validar categoría
            ProductoValidator.validar_categoria(data['categoria'])
            
            # 5. Validar precio
            ProductoValidator.validar_precio(data['precio_unitario'])
            
            # 6. Validar fechas
            fecha_vencimiento = ProductoValidator.validar_fecha(
                data['fecha_vencimiento'], 
                "fecha_vencimiento"
            )
            fecha_vencimiento_cert = ProductoValidator.validar_fecha(
                data['fecha_vencimiento_cert'],
                "fecha_vencimiento_cert"
            )
            
            # 7. Validar tipo de certificación
            ProductoValidator.validar_tipo_certificacion(data['tipo_certificacion'])
            
            # 8. Validar certificación
            CertificacionValidator.validar_certificacion_requerida(archivos_certificacion)
            for archivo in archivos_certificacion:
                CertificacionValidator.validar_archivo(archivo)
            
            # 9. Crear producto
            producto = Producto(
                nombre=data['nombre'],
                codigo_sku=data['codigo_sku'],
                categoria=data['categoria'],
                precio_unitario=float(data['precio_unitario']),
                condiciones_almacenamiento=data['condiciones_almacenamiento'],
                fecha_vencimiento=fecha_vencimiento,
                proveedor_id=int(data['proveedor_id']),
                usuario_registro=data['usuario_registro'],
                estado='Activo',  # Por defecto activo
                cantidad_disponible=int(data.get('cantidad_disponible', 0))  # Default 0 si no se proporciona
            )
            
            # 10. Agregar a sesión y hacer flush para obtener el ID
            db.session.add(producto)
            db.session.flush()
            
            # 11. Guardar certificación (solo una según requisitos)
            certificacion = ProductoService._guardar_certificacion(
                producto.id,
                archivos_certificacion[0],
                data['tipo_certificacion'],
                fecha_vencimiento_cert
            )
            db.session.add(certificacion)
            
            # 12. Commit final
            db.session.commit()
            
            return producto
            
        except ConflictError:
            db.session.rollback()
            raise
            
        except ValueError:
            db.session.rollback()
            raise
            
        except IntegrityError as e:
            db.session.rollback()
            if 'codigo_sku' in str(e):
                raise ConflictError({
                    "error": f"Ya existe un producto registrado con el SKU {data['codigo_sku']}",
                    "codigo": "SKU_DUPLICADO"
                })
            raise ValueError({"error": "Error al guardar el producto en la base de datos"})
        
        except Exception as e:
            db.session.rollback()
            raise ValueError({"error": f"Error inesperado: {str(e)}"})
    
    @staticmethod
    def _verificar_sku_existe(sku):
        """Verifica si ya existe un producto con el SKU dado"""
        return Producto.query.filter_by(codigo_sku=sku).first() is not None

    @staticmethod
    def _guardar_certificacion(producto_id, archivo, tipo_certificacion, fecha_vencimiento_cert):
        """Guarda un archivo de certificación en el sistema de archivos"""
        
        # Obtener el directorio base de uploads desde la configuración de Flask
        base_upload_dir = current_app.config['UPLOAD_FOLDER']
        
        # Crear ruta absoluta para el directorio de certificaciones del producto
        upload_dir = os.path.join(base_upload_dir, 'certificaciones_producto', str(producto_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        filename = secure_filename(archivo.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ruta absoluta completa del archivo
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        archivo.save(file_path)
        
        # Crear registro en base de datos con ruta absoluta
        certificacion = CertificacionProducto(
            producto_id=producto_id,
            tipo_certificacion=tipo_certificacion,
            nombre_archivo=filename,
            ruta_archivo=file_path,  # Ahora guarda ruta absoluta
            tamaño_archivo=os.path.getsize(file_path),
            fecha_vencimiento_cert=fecha_vencimiento_cert
        )
        
        return certificacion
