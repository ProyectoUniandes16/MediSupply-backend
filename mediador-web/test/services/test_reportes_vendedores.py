"""
Tests unitarios para la generación de reportes de ventas.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.vendedores import generar_reporte_ventas_vendedor, VendedorServiceError


class TestGenerarReporteVentas:
    """Tests para generar_reporte_ventas_vendedor"""
    
    @patch('src.services.vendedores.obtener_pedidos_vendedor')
    @patch('src.services.vendedores.listar_planes_venta_externo')
    @patch('src.services.vendedores.obtener_detalle_vendedor_externo')
    def test_generar_reporte_con_datos_completos(
        self, 
        mock_vendedor, 
        mock_planes, 
        mock_pedidos
    ):
        """Test: generar reporte con datos completos"""
        # Arrange
        mock_vendedor.return_value = {
            'id': 'v123',
            'nombre': 'Juan',
            'apellidos': 'Pérez',
            'correo': 'juan@test.com',
            'zona': 'Bogotá'
        }
        
        mock_planes.return_value = {
            'items': [
                {
                    'nombre_plan': 'Plan Q1',
                    'periodo': '2025-01',
                    'meta_ingresos': 50000.00,
                    'meta_visitas': 100,
                    'meta_clientes_nuevos': 20
                }
            ]
        }
        
        mock_pedidos.return_value = [
            {
                'id': 1,
                'total': 1500.50,
                'cliente_id': 100,
                'estado': 'completado',
                'fecha_pedido': '2025-01-15T10:30:00'
            },
            {
                'id': 2,
                'total': 2000.00,
                'cliente_id': 101,
                'estado': 'completado',
                'fecha_pedido': '2025-01-20T14:00:00'
            }
        ]
        
        # Act
        resultado = generar_reporte_ventas_vendedor('v123', 1, 2025)
        
        # Assert
        assert resultado['vendedor']['nombre_completo'] == 'Juan Pérez'
        assert resultado['periodo']['mes'] == 1
        assert resultado['periodo']['anio'] == 2025
        assert resultado['metricas']['ventas_realizadas'] == 2
        assert resultado['metricas']['monto_total'] == 3500.50
        assert resultado['metricas']['clientes_unicos'] == 2
        assert len(resultado['planes']) == 1
    
    @patch('src.services.vendedores.obtener_pedidos_vendedor')
    @patch('src.services.vendedores.listar_planes_venta_externo')
    @patch('src.services.vendedores.obtener_detalle_vendedor_externo')
    def test_generar_reporte_sin_ventas(
        self, 
        mock_vendedor, 
        mock_planes, 
        mock_pedidos
    ):
        """Test: generar reporte cuando no hay ventas"""
        # Arrange
        mock_vendedor.return_value = {
            'id': 'v123',
            'nombre': 'Juan',
            'apellidos': 'Pérez',
            'correo': 'juan@test.com',
            'zona': 'Bogotá'
        }
        
        mock_planes.return_value = {
            'items': [
                {
                    'nombre_plan': 'Plan Q1',
                    'periodo': '2025-01',
                    'meta_ingresos': 50000.00,
                    'meta_visitas': 100,
                    'meta_clientes_nuevos': 20
                }
            ]
        }
        
        mock_pedidos.return_value = []
        
        # Act
        resultado = generar_reporte_ventas_vendedor('v123', 1, 2025)
        
        # Assert
        assert resultado['metricas']['ventas_realizadas'] == 0
        assert resultado['metricas']['monto_total'] == 0
        assert resultado['metricas']['clientes_unicos'] == 0
        assert resultado['metricas']['cumplimiento_porcentaje'] == 0
    
    def test_generar_reporte_mes_invalido(self):
        """Test: error cuando el mes es inválido"""
        # Act & Assert
        with pytest.raises(VendedorServiceError) as exc:
            generar_reporte_ventas_vendedor('v123', 13, 2025)
        
        assert exc.value.status_code == 400
        assert 'MES_INVALIDO' in str(exc.value.message)
    
    def test_generar_reporte_anio_invalido(self):
        """Test: error cuando el año es inválido"""
        # Act & Assert
        with pytest.raises(VendedorServiceError) as exc:
            generar_reporte_ventas_vendedor('v123', 1, 2100)
        
        assert exc.value.status_code == 400
        assert 'ANIO_INVALIDO' in str(exc.value.message)
    
    @patch('src.services.vendedores.obtener_pedidos_vendedor')
    @patch('src.services.vendedores.listar_planes_venta_externo')
    @patch('src.services.vendedores.obtener_detalle_vendedor_externo')
    def test_generar_reporte_calcula_cumplimiento(
        self, 
        mock_vendedor, 
        mock_planes, 
        mock_pedidos
    ):
        """Test: verificar cálculo de porcentaje de cumplimiento"""
        # Arrange
        mock_vendedor.return_value = {
            'id': 'v123',
            'nombre': 'Juan',
            'apellidos': 'Pérez',
            'correo': 'juan@test.com',
            'zona': 'Bogotá'
        }
        
        mock_planes.return_value = {
            'items': [
                {
                    'nombre_plan': 'Plan Q1',
                    'periodo': '2025-01',
                    'meta_ingresos': 10000.00,
                    'meta_visitas': 100,
                    'meta_clientes_nuevos': 20
                }
            ]
        }
        
        mock_pedidos.return_value = [
            {
                'id': 1,
                'total': 5000.00,  # 50% de la meta
                'cliente_id': 100,
                'estado': 'completado',
                'fecha_pedido': '2025-01-15T10:30:00'
            }
        ]
        
        # Act
        resultado = generar_reporte_ventas_vendedor('v123', 1, 2025)
        
        # Assert
        assert resultado['metricas']['monto_total'] == 5000.00
        assert resultado['metricas']['meta_ingresos_total'] == 10000.00
        assert resultado['metricas']['cumplimiento_porcentaje'] == 50.00
