"""
Tests para las rutas de Plan de Venta - KAN-86
"""
import pytest
import json
from uuid import uuid4
from app.models.vendedor import Vendedor
from app.models import db


@pytest.fixture
def vendedor_test(app_ctx):
    """Fixture para crear un vendedor de prueba"""
    vendedor = Vendedor(
        id=str(uuid4()),
        nombre="María",
        apellidos="González",
        correo="maria.gonzalez@test.com",
        telefono="9876543210",
        estado="activo"
    )
    db.session.add(vendedor)
    db.session.commit()
    vendedor_id = vendedor.id
    yield vendedor_id
    # Cleanup se hace automáticamente por app_ctx


class TestPostPlanVenta:
    """Tests para POST /v1/planes-venta"""
    
    def test_crear_plan_exitoso(self, client, vendedor_test):
        """Debe crear un plan de venta exitosamente con vendedores_ids"""
        payload = {
            "nombre_plan": "Plan Trimestre Q1",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-01",
            "meta_ingresos": 75000.50,
            "meta_visitas": 150,
            "meta_clientes_nuevos": 30
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["nombre_plan"] == "Plan Trimestre Q1"
        assert data["periodo"] == "2025-01"
        assert data["meta_ingresos"] == 75000.50
        assert data["meta_visitas"] == 150
        assert data["meta_clientes_nuevos"] == 30
        assert data["estado"] == "activo"
        assert data["operacion"] == "crear"
        assert "id" in data
        assert "vendedores" in data
        assert len(data["vendedores"]) == 1
        assert data["vendedores"][0]["id"] == vendedor_test
    
    def test_actualizar_plan_existente(self, client, vendedor_test):
        """Debe actualizar un plan existente usando plan_id"""
        # Crear plan inicial
        payload_inicial = {
            "nombre_plan": "Plan Original",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-02",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        response1 = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload_inicial),
            content_type="application/json"
        )
        assert response1.status_code == 201
        plan_id = response1.get_json()["id"]
        
        # Actualizar usando plan_id
        payload_actualizado = {
            "plan_id": plan_id,
            "nombre_plan": "Plan Actualizado",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-02",
            "meta_ingresos": 80000.00,
            "meta_visitas": 200,
            "meta_clientes_nuevos": 40
        }
        
        response2 = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload_actualizado),
            content_type="application/json"
        )
        
        assert response2.status_code == 200  # 200 para actualización
        data = response2.get_json()
        assert data["id"] == plan_id  # mismo ID
        assert data["nombre_plan"] == "Plan Actualizado"
        assert data["meta_ingresos"] == 80000.00
        assert data["operacion"] == "actualizar"
    
    def test_crear_plan_campos_faltantes(self, client):
        """Debe retornar 400 si faltan campos obligatorios"""
        payload = {
            "nombre_plan": "Plan Incompleto"
            # Faltan campos obligatorios
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        # El error puede venir como string directamente o en un campo error
        assert "error" in data or "obligatorios" in str(data).lower()
    
    def test_crear_plan_vendedor_no_existe(self, client):
        """Debe retornar 404 si algún vendedor no existe"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [str(uuid4())],  # vendedor que no existe
            "periodo": "2025-03",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["codigo"] == "VENDEDORES_NO_ENCONTRADOS"
    
    def test_crear_plan_periodo_invalido(self, client, vendedor_test):
        """Debe retornar 400 si el formato del periodo es inválido"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025/04",  # formato inválido
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["codigo"] == "FORMATO_PERIODO_INVALIDO"
    
    def test_crear_plan_meta_negativa(self, client, vendedor_test):
        """Debe retornar 400 si alguna meta es negativa"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-05",
            "meta_ingresos": 50000.00,
            "meta_visitas": -10,  # negativo
            "meta_clientes_nuevos": 20
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["codigo"] == "VALOR_NEGATIVO"
    
    def test_crear_plan_formato_numerico_invalido(self, client, vendedor_test):
        """Debe retornar 400 si el formato numérico es inválido"""
        payload = {
            "nombre_plan": "Plan Test",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-06",
            "meta_ingresos": "no_es_numero",  # inválido
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["codigo"] == "FORMATO_NUMERICO_INVALIDO"
    
    def test_crear_plan_con_estado_custom(self, client, vendedor_test):
        """Debe permitir especificar un estado personalizado"""
        payload = {
            "nombre_plan": "Plan Inactivo",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-07",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20,
            "estado": "inactivo"
        }
        
        response = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["estado"] == "inactivo"


class TestGetPlanVenta:
    """Tests para GET /v1/planes-venta/{plan_id}"""
    
    def test_obtener_plan_existente(self, client, vendedor_test):
        """Debe obtener un plan existente por su ID con vendedores"""
        # Crear plan
        payload = {
            "nombre_plan": "Plan Para Obtener",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-08",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        
        response_create = client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        plan_id = response_create.get_json()["id"]
        
        # Obtener plan
        response = client.get(f"/v1/planes-venta/{plan_id}")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == plan_id
        assert data["nombre_plan"] == "Plan Para Obtener"
        assert "vendedores" in data
        assert len(data["vendedores"]) == 1
    
    def test_obtener_plan_no_existente(self, client):
        """Debe retornar 404 si el plan no existe"""
        plan_id_falso = str(uuid4())
        
        response = client.get(f"/v1/planes-venta/{plan_id_falso}")
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["codigo"] == "PLAN_NO_ENCONTRADO"


class TestGetPlanesVenta:
    """Tests para GET /v1/planes-venta (listar)"""
    
    def test_listar_planes(self, client, vendedor_test):
        """Debe listar planes de venta con vendedores"""
        # Crear algunos planes
        for i in range(3):
            payload = {
                "nombre_plan": f"Plan {i+1}",
                "gerente_id": str(uuid4()),
                "vendedores_ids": [vendedor_test],
                "periodo": f"2025-{i+1:02d}",
                "meta_ingresos": 50000.00 * (i+1),
                "meta_visitas": 100 * (i+1),
                "meta_clientes_nuevos": 20 * (i+1)
            }
            client.post(
                "/v1/planes-venta",
                data=json.dumps(payload),
                content_type="application/json"
            )
        
        # Listar
        response = client.get("/v1/planes-venta")
        
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3
        # Verificar que cada plan tiene vendedores
        for plan in data["items"]:
            assert "vendedores" in plan
    
    def test_listar_filtrado_por_vendedor(self, client, vendedor_test):
        """Debe filtrar planes que contengan un vendedor específico"""
        # Crear plan para este vendedor
        payload = {
            "nombre_plan": "Plan Específico",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-09",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
        }
        client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        # Listar solo de este vendedor
        response = client.get(f"/v1/planes-venta?vendedor_id={vendedor_test}")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] > 0
        # Verificar que el vendedor está en la lista de vendedores de cada plan
        for plan in data["items"]:
            vendedor_ids = [v["id"] for v in plan["vendedores"]]
            assert vendedor_test in vendedor_ids
    
    def test_listar_con_paginacion(self, client):
        """Debe soportar paginación"""
        response = client.get("/v1/planes-venta?page=1&size=5")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert "pages" in data
