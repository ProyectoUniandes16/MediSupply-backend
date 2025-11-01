"""
Servicio para consultar inventarios (usa cache primero, fallback a microservicio).
"""
import requests
import logging
from typing import List, Dict, Any, Optional
from flask import current_app
from src.services.cache_client import CacheClient

logger = logging.getLogger(__name__)


class InventariosService:
    """Servicio para consultar inventarios con estrategia cache-first."""
    
    @staticmethod
    def _get_cache_client() -> CacheClient:
        """Obtiene una instancia del cliente de cache."""
        redis_url = current_app.config.get('REDIS_SERVICE_URL')
        return CacheClient(redis_url)
    
    @staticmethod
    def _get_from_microservice(producto_id: str) -> List[Dict[str, Any]]:
        """
        Consulta inventarios directamente del microservicio (fallback).
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Lista de inventarios
        """
        try:
            inventarios_url = current_app.config.get('INVENTARIOS_URL')
            
            response = requests.get(
                f"{inventarios_url}/api/inventarios",
                params={'productoId': producto_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                inventarios = data.get('inventarios', [])
                logger.info(f"✅ Inventarios obtenidos del microservicio: {len(inventarios)} items")
                return inventarios
            else:
                logger.error(f"❌ Error consultando microservicio: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error consultando microservicio de inventarios: {e}")
            return []
    
    @staticmethod
    def get_inventarios_by_producto(producto_id: str) -> Dict[str, Any]:
        """
        Obtiene inventarios de un producto (cache-first strategy).
        
        1. Intenta leer del cache
        2. Si no está en cache, consulta el microservicio
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Diccionario con inventarios y metadata
        """
        cache_client = InventariosService._get_cache_client()
        
        # Intentar obtener del cache
        inventarios = cache_client.get_inventarios_by_producto(producto_id)
        source = 'cache'
        current_app.logger.info(f"inventarios: {inventarios}")
        
        # Si no está en cache, consultar microservicio
        if inventarios is None:
            current_app.logger.info(f"📡 Consultando microservicio para producto {producto_id}")
            inventarios = InventariosService._get_from_microservice(producto_id)
            source = 'microservice'
        
        # Calcular totales
        total_cantidad = sum(inv.get('cantidad', 0) for inv in inventarios)
        
        return {
            'data': {
                'productoId': producto_id,
                'inventarios': inventarios,
                'total': len(inventarios),
                'totalCantidad': total_cantidad,
                'source': source  # Útil para debugging
            }
        }
    
    @staticmethod
    def get_total_disponible(producto_id: str) -> int:
        """
        Obtiene el total de unidades disponibles de un producto.
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Total de unidades disponibles
        """
        result = InventariosService.get_inventarios_by_producto(producto_id)
        return result.get('totalCantidad', 0)
    
    @staticmethod
    def crear_inventario(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo inventario (delega al microservicio).
        
        El microservicio se encarga de:
        1. Guardar en BD
        2. Encolar mensaje para actualización de cache
        
        Args:
            data: Datos del inventario a crear
        
        Returns:
            Inventario creado
        
        Raises:
            Exception si falla la creación
        """
        try:
            inventarios_url = current_app.config.get('INVENTARIOS_URL')
            
            response = requests.post(
                f"{inventarios_url}/api/inventarios",
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                inventario = response.json()
                logger.info(f"✅ Inventario creado: {inventario.get('id')}")
                return inventario
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f'Error {response.status_code}')
                logger.error(f"❌ Error creando inventario: {error_msg}")
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            logger.error(f"❌ Error de conexión creando inventario: {e}")
            raise Exception(f"Error de conexión: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error creando inventario: {e}")
            raise
    
    @staticmethod
    def actualizar_inventario(inventario_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un inventario existente (delega al microservicio).
        
        Args:
            inventario_id: ID del inventario
            data: Datos a actualizar
        
        Returns:
            Inventario actualizado
        """
        try:
            inventarios_url = current_app.config.get('INVENTARIOS_URL')
            
            response = requests.put(
                f"{inventarios_url}/api/inventarios/{inventario_id}",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                inventario = response.json()
                logger.info(f"✅ Inventario actualizado: {inventario_id}")
                return inventario
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f'Error {response.status_code}')
                logger.error(f"❌ Error actualizando inventario: {error_msg}")
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            logger.error(f"❌ Error de conexión actualizando inventario: {e}")
            raise Exception(f"Error de conexión: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error actualizando inventario: {e}")
            raise
    
    @staticmethod
    def eliminar_inventario(inventario_id: str, usuario: Optional[str] = None) -> bool:
        """
        Elimina un inventario (delega al microservicio).
        
        Args:
            inventario_id: ID del inventario
            usuario: Usuario que realiza la eliminación
        
        Returns:
            True si se eliminó correctamente
        """
        try:
            inventarios_url = current_app.config.get('INVENTARIOS_URL')
            
            payload = {'usuario': usuario} if usuario else {}
            
            response = requests.delete(
                f"{inventarios_url}/api/inventarios/{inventario_id}",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Inventario eliminado: {inventario_id}")
                return True
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f'Error {response.status_code}')
                logger.error(f"❌ Error eliminando inventario: {error_msg}")
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            logger.error(f"❌ Error de conexión eliminando inventario: {e}")
            raise Exception(f"Error de conexión: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error eliminando inventario: {e}")
            raise
    
    @staticmethod
    def ajustar_cantidad(inventario_id: str, ajuste: int, usuario: Optional[str] = None) -> Dict[str, Any]:
        """
        Ajusta la cantidad de un inventario (delega al microservicio).
        
        Args:
            inventario_id: ID del inventario
            ajuste: Cantidad a sumar o restar
            usuario: Usuario que realiza el ajuste
        
        Returns:
            Inventario actualizado
        """
        try:
            inventarios_url = current_app.config.get('INVENTARIOS_URL')
            
            payload = {
                'ajuste': ajuste,
                'usuario': usuario or 'sistema'
            }
            
            response = requests.post(
                f"{inventarios_url}/api/inventarios/{inventario_id}/ajustar",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                inventario = response.json()
                logger.info(f"✅ Cantidad ajustada: {inventario_id} ({ajuste:+d})")
                return inventario
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f'Error {response.status_code}')
                logger.error(f"❌ Error ajustando cantidad: {error_msg}")
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            logger.error(f"❌ Error de conexión ajustando cantidad: {e}")
            raise Exception(f"Error de conexión: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error ajustando cantidad: {e}")
            raise
