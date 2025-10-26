"""
Tests para el servicio de Plan de Venta - KAN-86
"""
import pytest
from decimal import Decimal
from app.services.plan_venta_service import (
    crear_o_actualizar_plan_venta,
    obtener_plan_venta,
    listar_planes_venta,
    validar_periodo,
    validar_decimal_no_negativo,
    validar_entero_no_negativo
)
from app.services import ValidationError, NotFoundError, ConflictError
from app.models.vendedor import Vendedor
from app.models.plan_venta import PlanVenta
from app.models import db
from uuid import uuid4


@pytest.fixture
def vendedor_test(app_ctx):
    """Fixture para crear un vendedor de prueba"""
    vendedor = Vendedor(
        id=str(uuid4()),
        nombre="Juan",
        apellidos="Pérez",
        correo="juan.perez@test.com",
        telefono="1234567890",
        estado="activo"
    )
    db.session.add(vendedor)
    db.session.commit()
    yield vendedor
    # Cleanup se hace automáticamente por app_ctx


class TestValidarPeriodo:
    """Tests para validación de periodo"""
    
    def test_periodo_valido(self):
        """Debe aceptar periodos con formato YYYY-MM válido"""
        validar_periodo("2025-01")
        validar_periodo("2025-12")
        validar_periodo("2024-06")
        # No debe lanzar excepción
        assert True
    
    def test_periodo_invalido_formato(self):
        """Debe rechazar periodos con formato inválido"""
        with pytest.raises(ValidationError) as exc_info:
            validar_periodo("2025/01")
        assert exc_info.value.message["codigo"] == "FORMATO_PERIODO_INVALIDO"
        
        with pytest.raises(ValidationError):
            validar_periodo("25-01")
        
        with pytest.raises(ValidationError):
            validar_periodo("2025-13")  # mes inválido
        
        with pytest.raises(ValidationError):
            validar_periodo("2025-00")  # mes inválido
    
    def test_periodo_vacio_o_none(self):
        """Debe rechazar periodos vacíos o None"""
        with pytest.raises(ValidationError) as exc_info:
            validar_periodo("")
        assert exc_info.value.message["codigo"] == "PERIODO_REQUERIDO"
        
        with pytest.raises(ValidationError):
            validar_periodo(None)
    
    def test_periodo_anio_fuera_de_rango(self):
        """Debe rechazar años fuera del rango 2020-2050"""
        with pytest.raises(ValidationError) as exc_info:
            validar_periodo("2019-01")
        assert exc_info.value.message["codigo"] == "ANIO_FUERA_DE_RANGO"
        
        with pytest.raises(ValidationError):
            validar_periodo("2051-01")


class TestValidarDecimalNoNegativo:
    """Tests para validación de decimales no negativos"""
    
    def test_decimal_valido(self):
        """Debe aceptar decimales válidos"""
        assert validar_decimal_no_negativo(100.50, "test") == Decimal("100.50")
        assert validar_decimal_no_negativo(0, "test") == Decimal("0")
        assert validar_decimal_no_negativo("50.25", "test") == Decimal("50.25")
    
    def test_decimal_negativo(self):
        """Debe rechazar valores negativos"""
        with pytest.raises(ValidationError) as exc_info:
            validar_decimal_no_negativo(-10.5, "meta_ingresos")
        assert exc_info.value.message["codigo"] == "VALOR_NEGATIVO"
    
    def test_decimal_invalido(self):
        """Debe rechazar formatos inválidos"""
        with pytest.raises(ValidationError) as exc_info:
            validar_decimal_no_negativo("abc", "meta_ingresos")
        assert exc_info.value.message["codigo"] == "FORMATO_NUMERICO_INVALIDO"
    
    def test_decimal_none(self):
        """Debe rechazar None"""
        with pytest.raises(ValidationError) as exc_info:
            validar_decimal_no_negativo(None, "meta_ingresos")
        assert exc_info.value.message["codigo"] == "CAMPO_REQUERIDO"


class TestValidarEnteroNoNegativo:
    """Tests para validación de enteros no negativos"""
    
    def test_entero_valido(self):
        """Debe aceptar enteros válidos"""
        assert validar_entero_no_negativo(100, "test") == 100
        assert validar_entero_no_negativo(0, "test") == 0
        assert validar_entero_no_negativo("50", "test") == 50
    
    def test_entero_negativo(self):
        """Debe rechazar valores negativos"""
        with pytest.raises(ValidationError) as exc_info:
            validar_entero_no_negativo(-10, "meta_visitas")
        assert exc_info.value.message["codigo"] == "VALOR_NEGATIVO"
    
    def test_entero_invalido(self):
        """Debe rechazar formatos inválidos"""
        with pytest.raises(ValidationError) as exc_info:
            validar_entero_no_negativo("abc", "meta_visitas")
        assert exc_info.value.message["codigo"] == "FORMATO_ENTERO_INVALIDO"
        
        # Nota: int(10.5) convierte a 10, no lanza error
        # Para validar que NO sea decimal, se requiere validación adicional


class TestCrearOActualizarPlanVenta:
    """Tests para crear o actualizar plan de venta"""
    
    def test_crear_plan_exitoso(self, app_ctx, vendedor_test):
        """Debe crear un nuevo plan de venta exitosamente"""
        payload = {
            "nombre_plan": "Plan Q1 2025",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-01",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        result = crear_o_actualizar_plan_venta(payload)
        
        assert result["operacion"] == "crear"
        assert result["nombre_plan"] == "Plan Q1 2025"
        assert result["vendedor_id"] == vendedor_test.id
        assert result["periodo"] == "2025-01"
        assert result["meta_ingresos"] == 50000.00
        assert result["meta_visitas"] == 100
        assert result["meta_clientes_nuevos"] == 20
        assert result["estado"] == "activo"
        assert "id" in result
    
    def test_actualizar_plan_existente(self, app_ctx, vendedor_test):
        """Debe actualizar un plan existente (UPSERT)"""
        # Crear plan inicial
        payload_inicial = {
            "nombre_plan": "Plan Inicial",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-02",
            "meta_ingresos": 30000.00,
            "meta_visitas": 50,
            "meta_clientes_nuevos": 10
        }
        result1 = crear_o_actualizar_plan_venta(payload_inicial)
        plan_id = result1["id"]
        
        # Actualizar el mismo plan (mismo vendedor_id y periodo)
        payload_actualizado = {
            "nombre_plan": "Plan Actualizado",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-02",  # mismo periodo
            "meta_ingresos": 60000.00,  # valores actualizados
            "meta_visitas": 120,
            "meta_clientes_nuevos": 25
        }
        result2 = crear_o_actualizar_plan_venta(payload_actualizado)
        
        assert result2["operacion"] == "actualizar"
        assert result2["id"] == plan_id  # mismo ID
        assert result2["nombre_plan"] == "Plan Actualizado"
        assert result2["meta_ingresos"] == 60000.00
        assert result2["meta_visitas"] == 120
    
    def test_crear_plan_campos_faltantes(self, app_ctx):
        """Debe rechazar si faltan campos obligatorios"""
        payload = {
            "nombre_plan": "Plan Test"
            # Faltan otros campos
        }
        
        with pytest.raises(ValidationError) as exc_info:
            crear_o_actualizar_plan_venta(payload)
        
        # El mensaje puede ser string o dict
        error_msg = exc_info.value.message
        if isinstance(error_msg, dict):
            assert "requerido" in error_msg.get("error", "").lower()
        else:
            assert "obligatorios" in str(error_msg).lower() or "requerido" in str(error_msg).lower()
    
    def test_crear_plan_vendedor_no_existe(self, app_ctx):
        """Debe rechazar si el vendedor no existe"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedor_id": str(uuid4()),  # vendedor que no existe
            "periodo": "2025-03",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        with pytest.raises(NotFoundError) as exc_info:
            crear_o_actualizar_plan_venta(payload)
        
        assert exc_info.value.message["codigo"] == "VENDEDOR_NO_ENCONTRADO"
    
    def test_crear_plan_periodo_invalido(self, app_ctx, vendedor_test):
        """Debe rechazar periodos con formato inválido"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025/03",  # formato inválido
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        with pytest.raises(ValidationError) as exc_info:
            crear_o_actualizar_plan_venta(payload)
        
        assert exc_info.value.message["codigo"] == "FORMATO_PERIODO_INVALIDO"
    
    def test_crear_plan_metas_negativas(self, app_ctx, vendedor_test):
        """Debe rechazar metas negativas"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-04",
            "meta_ingresos": -1000.00,  # negativo
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        with pytest.raises(ValidationError) as exc_info:
            crear_o_actualizar_plan_venta(payload)
        
        assert exc_info.value.message["codigo"] == "VALOR_NEGATIVO"
    
    def test_crear_plan_nombre_muy_corto(self, app_ctx, vendedor_test):
        """Debe rechazar nombres de plan muy cortos"""
        payload = {
            "nombre_plan": "AB",  # muy corto
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-05",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        with pytest.raises(ValidationError) as exc_info:
            crear_o_actualizar_plan_venta(payload)
        
        assert exc_info.value.message["codigo"] == "NOMBRE_PLAN_INVALIDO"
    
    def test_crear_plan_con_estado_personalizado(self, app_ctx, vendedor_test):
        """Debe permitir especificar estado personalizado"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-06",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20,
            "estado": "inactivo"
        }
        
        result = crear_o_actualizar_plan_venta(payload)
        assert result["estado"] == "inactivo"


class TestObtenerPlanVenta:
    """Tests para obtener plan de venta por ID"""
    
    def test_obtener_plan_existente(self, app_ctx, vendedor_test):
        """Debe obtener un plan existente"""
        # Crear plan
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-07",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        plan_creado = crear_o_actualizar_plan_venta(payload)
        
        # Obtener plan
        plan_obtenido = obtener_plan_venta(plan_creado["id"])
        
        assert plan_obtenido["id"] == plan_creado["id"]
        assert plan_obtenido["nombre_plan"] == "Plan Test"
    
    def test_obtener_plan_no_existente(self, app_ctx):
        """Debe lanzar NotFoundError si el plan no existe"""
        with pytest.raises(NotFoundError) as exc_info:
            obtener_plan_venta(str(uuid4()))
        
        assert exc_info.value.message["codigo"] == "PLAN_NO_ENCONTRADO"


class TestListarPlanesVenta:
    """Tests para listar planes de venta"""
    
    def test_listar_todos_los_planes(self, app_ctx, vendedor_test):
        """Debe listar todos los planes"""
        # Crear varios planes
        for i in range(3):
            payload = {
                "nombre_plan": f"Plan {i}",
                "gerente_id": str(uuid4()),
                "vendedor_id": vendedor_test.id,
                "periodo": f"2025-{i+1:02d}",
                "meta_ingresos": 50000.00 * (i+1),
                "meta_visitas": 100 * (i+1),
                "meta_clientes_nuevos": 20 * (i+1)
            }
            crear_o_actualizar_plan_venta(payload)
        
        # Listar
        result = listar_planes_venta()
        
        assert result["total"] >= 3
        assert len(result["items"]) >= 3
        assert result["page"] == 1
    
    def test_listar_filtrado_por_vendedor(self, app_ctx, vendedor_test):
        """Debe filtrar planes por vendedor"""
        # Crear plan para este vendedor
        payload = {
            "nombre_plan": "Plan Vendedor Específico",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test.id,
            "periodo": "2025-08",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        crear_o_actualizar_plan_venta(payload)
        
        # Listar solo planes de este vendedor
        result = listar_planes_venta(vendedor_id=vendedor_test.id)
        
        assert result["total"] > 0
        for plan in result["items"]:
            assert plan["vendedor_id"] == vendedor_test.id
    
    def test_listar_con_paginacion(self, app_ctx, vendedor_test):
        """Debe soportar paginación"""
        result = listar_planes_venta(page=1, size=5)
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert result["page"] == 1
        assert result["size"] == 5
