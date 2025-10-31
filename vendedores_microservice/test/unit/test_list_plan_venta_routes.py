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
        """Debe crear un plan de venta exitosamente"""
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
        assert "vendedores" in data
        assert len(data["vendedores"]) == 1
        assert data["vendedores"][0]["id"] == vendedor_test
        assert data["periodo"] == "2025-01"
        assert data["meta_ingresos"] == 75000.50
        assert data["meta_visitas"] == 150
        assert data["meta_clientes_nuevos"] == 30
        assert data["estado"] == "activo"
        assert data["operacion"] == "crear"
        assert "id" in data
    
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
    """Tests para GET /v1/planes-venta (listar) - KAN-87"""
    
    def test_listar_planes_basico(self, client, vendedor_test):
        """Debe listar planes de venta con estructura correcta"""
        # Crear un plan
        payload = {
            "nombre_plan": "Plan Q1 2025",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-01",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20
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
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert data["total"] >= 1
        
        # Verificar que incluye información de vendedores
        if len(data["items"]) > 0:
            plan = data["items"][0]
            assert "vendedores" in plan
            assert len(plan["vendedores"]) > 0
            assert plan["vendedores"][0]["nombre"] == "María"
            assert plan["vendedores"][0]["apellidos"] == "González"
    
    def test_bdd_listado_paginado(self, client, vendedor_test, app_ctx):
        """
        BDD: Listado paginado
        Dado que hay más de size planes,
        Cuando solicito page y size,
        Entonces recibo items, page, size y total, ordenados por fechaCreacion desc.
        """
        # Crear múltiples vendedores y planes para evitar conflictos de unique constraint
        vendedores_ids = [vendedor_test]
        
        # Crear vendedores adicionales
        for i in range(2):
            vendedor = Vendedor(
                id=str(uuid4()),
                nombre=f"Vendedor{i+2}",
                apellidos="Test",
                correo=f"vendedor{i+2}@test.com",
                estado="activo"
            )
            db.session.add(vendedor)
            vendedores_ids.append(vendedor.id)
        db.session.commit()
        
        # Crear 15 planes distribuidos entre los vendedores
        for i in range(15):
            vendedor_idx = i % len(vendedores_ids)
            periodo_num = (i // len(vendedores_ids)) + 1
            
            payload = {
                "nombre_plan": f"Plan {i+1:02d}",
                "gerente_id": str(uuid4()),
                "vendedores_ids": [vendedores_ids[vendedor_idx]],
                "periodo": f"2025-{periodo_num:02d}",
                "meta_ingresos": 50000.00 + (i * 1000),
                "meta_visitas": 100 + (i * 10),
                "meta_clientes_nuevos": 20 + i
            }
            response = client.post(
                "/v1/planes-venta",
                data=json.dumps(payload),
                content_type="application/json"
            )
            # Asegurar que todos se crearon exitosamente
            assert response.status_code == 201
        
        # Solicitar página 1 con tamaño 5
        response = client.get("/v1/planes-venta?page=1&size=5")
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verificar estructura de paginación
        assert data["page"] == 1
        assert data["size"] == 5
        assert len(data["items"]) == 5
        assert data["total"] == 15
        assert data["pages"] == 3
        
        # Verificar orden descendente por fecha de creación
        # Los planes deben estar ordenados, los más recientes primero
        fechas_creacion = [item["fecha_creacion"] for item in data["items"]]
        for i in range(len(fechas_creacion) - 1):
            # fecha[i] debe ser >= fecha[i+1] (orden descendente)
            assert fechas_creacion[i] >= fechas_creacion[i+1], \
                f"Orden incorrecto: {fechas_creacion[i]} debe ser >= {fechas_creacion[i+1]}"
    
    def test_bdd_filtro_por_vendedor(self, client, vendedor_test, app_ctx):
        """
        BDD: Filtro por vendedor
        Dado un vendedorId específico,
        Cuando aplico el filtro,
        Entonces la lista muestra solo los planes de ese vendedor.
        """
        # Crear otro vendedor
        otro_vendedor = Vendedor(
            id=str(uuid4()),
            nombre="Pedro",
            apellidos="Martínez",
            correo="pedro.martinez@test.com",
            estado="activo"
        )
        db.session.add(otro_vendedor)
        db.session.commit()
        
        # Crear planes para vendedor_test
        for i in range(3):
            payload = {
                "nombre_plan": f"Plan María {i+1}",
                "gerente_id": str(uuid4()),
                "vendedores_ids": [vendedor_test],
                "periodo": f"2025-{i+1:02d}",
                "meta_ingresos": 50000.00,
                "meta_visitas": 100,
                "meta_clientes_nuevos": 20
            }
            client.post(
                "/v1/planes-venta",
                data=json.dumps(payload),
                content_type="application/json"
            )
        
        # Crear planes para otro vendedor
        for i in range(2):
            payload = {
                "nombre_plan": f"Plan Pedro {i+1}",
                "gerente_id": str(uuid4()),
                "vendedores_ids": [otro_vendedor.id],
                "periodo": f"2025-{i+4:02d}",
                "meta_ingresos": 40000.00,
                "meta_visitas": 80,
                "meta_clientes_nuevos": 15
            }
            client.post(
                "/v1/planes-venta",
                data=json.dumps(payload),
                content_type="application/json"
            )
        
        # Filtrar por vendedor_test
        response = client.get(f"/v1/planes-venta?vendedor_id={vendedor_test}")
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Todos los planes deben contener al vendedor_test
        assert data["total"] == 3
        for plan in data["items"]:
            vendedor_ids = [v["id"] for v in plan["vendedores"]]
            assert vendedor_test in vendedor_ids
            assert plan["vendedores"][0]["nombre"] == "María"
            assert "María" in plan["nombre_plan"]
    
    def test_bdd_sin_resultados(self, client):
        """
        BDD: Sin resultados
        Dado filtros que no coinciden con registros,
        Cuando consulto,
        Entonces recibo items = [], total = 0.
        """
        vendedor_inexistente = str(uuid4())
        
        response = client.get(f"/v1/planes-venta?vendedor_id={vendedor_inexistente}")
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["pages"] == 0
    
    def test_filtrar_por_periodo(self, client, vendedor_test):
        """Debe filtrar planes por periodo específico"""
        # Crear planes de diferentes periodos
        periodos = ["2025-01", "2025-02", "2025-03"]
        for periodo in periodos:
            payload = {
                "nombre_plan": f"Plan {periodo}",
                "gerente_id": str(uuid4()),
                "vendedores_ids": [vendedor_test],
                "periodo": periodo,
                "meta_ingresos": 50000.00,
                "meta_visitas": 100,
                "meta_clientes_nuevos": 20
            }
            client.post(
                "/v1/planes-venta",
                data=json.dumps(payload),
                content_type="application/json"
            )
        
        # Filtrar por periodo específico
        response = client.get("/v1/planes-venta?periodo=2025-02")
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Solo debe retornar planes del periodo 2025-02
        assert data["total"] >= 1
        for plan in data["items"]:
            assert plan["periodo"] == "2025-02"
    
    def test_filtrar_por_estado(self, client, vendedor_test):
        """Debe filtrar planes por estado"""
        # Crear planes con diferentes estados
        estados = ["activo", "inactivo"]
        for i, estado in enumerate(estados):
            payload = {
                "nombre_plan": f"Plan {estado}",
                "gerente_id": str(uuid4()),
                "vendedores_ids": [vendedor_test],
                "periodo": f"2025-{i+10:02d}",
                "meta_ingresos": 50000.00,
                "meta_visitas": 100,
                "meta_clientes_nuevos": 20,
                "estado": estado
            }
            client.post(
                "/v1/planes-venta",
                data=json.dumps(payload),
                content_type="application/json"
            )
        
        # Filtrar por estado activo
        response = client.get("/v1/planes-venta?estado=activo")
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Todos deben ser activos
        for plan in data["items"]:
            assert plan["estado"] == "activo"
    
    def test_multiples_filtros_combinados(self, client, vendedor_test):
        """Debe permitir combinar múltiples filtros"""
        # Crear plan específico
        payload = {
            "nombre_plan": "Plan Específico Combinado",
            "gerente_id": str(uuid4()),
            "vendedores_ids": [vendedor_test],
            "periodo": "2025-12",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20,
            "estado": "activo"
        }
        client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        # Filtrar combinando vendedor, periodo y estado
        response = client.get(
            f"/v1/planes-venta?vendedor_id={vendedor_test}&periodo=2025-12&estado=activo"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["total"] >= 1
        for plan in data["items"]:
            vendedor_ids = [v["id"] for v in plan["vendedores"]]
            assert vendedor_test in vendedor_ids
            assert plan["periodo"] == "2025-12"
            assert plan["estado"] == "activo"
    
    def test_validar_paginacion_limites(self, client):
        """Debe validar y ajustar límites de paginación"""
        # Page < 1 debe ajustarse a 1
        response = client.get("/v1/planes-venta?page=0&size=10")
        assert response.status_code == 200
        data = response.get_json()
        assert data["page"] == 1
        
        # Size > 100 debe ajustarse a 10
        response = client.get("/v1/planes-venta?page=1&size=150")
        assert response.status_code == 200
        data = response.get_json()
        assert data["size"] == 10
        
        # Size < 1 debe ajustarse a 10
        response = client.get("/v1/planes-venta?page=1&size=0")
        assert response.status_code == 200
        data = response.get_json()
        assert data["size"] == 10
    
    def test_columnas_requeridas_en_respuesta(self, client, vendedor_test):
        """Debe incluir todas las columnas requeridas por KAN-87"""
        # Crear plan
        payload = {
            "nombre_plan": "Plan Test Columnas",
            "gerente_id": str(uuid4()),
            "vendedor_id": vendedor_test,
            "periodo": "2025-11",
            "meta_ingresos": 2000000.00,
            "meta_visitas": 20,
            "meta_clientes_nuevos": 4,
            "estado": "activo"
        }
        client.post(
            "/v1/planes-venta",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        response = client.get("/v1/planes-venta")
        
        assert response.status_code == 200
        data = response.get_json()
        
        if len(data["items"]) > 0:
            plan = data["items"][0]
            
            # Verificar columnas según mockup
            assert "id" in plan  # ID Plan
            assert "nombre_plan" in plan  # Nombre Plan
            assert "vendedor" in plan  # Información del vendedor
            assert "vendedor_nombre_completo" in plan  # Nombre completo vendedor
            assert "periodo" in plan  # Periodo (YYYY-MM)
            assert "meta_ingresos" in plan  # Meta de Ingresos
            assert "meta_visitas" in plan  # Meta de Visitas
            assert "meta_clientes_nuevos" in plan  # Meta Clientes Nuevos
            assert "estado" in plan  # Estado
