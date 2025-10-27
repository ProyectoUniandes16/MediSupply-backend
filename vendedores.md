# Microservicio Vendedores - Contratos API# Microservicio Vendedores - Contratos API



## 📋 Información General

- **Servicio**: `vendedores-service`

- **Base URL**: `http://localhost:5007`## 📋 Información General## 📋 Información General

- **Formato**: JSON (requests/responses)

- **Autenticación**: No implementada (pendiente)- **Servicio**: `vendedores-service`- **Servicio**: `vendedores-service`

- **Dependencias**: PostgreSQL 16

- **Convenciones**:- **Base URL**: `http://localhost:5007`- **Base URL**: `http://localhost:8001/v1`

  - **DB**: `snake_case`

  - **API/JSON**: `snake_case`- **Formato**: JSON (requests/responses)- **Formato**: JSON (requests/responses)



---- **Autenticación**: No implementada (pendiente)- **Autenticación**: No implementada (pendiente)



## 📌 Endpoints- **Dependencias**: PostgreSQL 16- **Dependencias**: PostgreSQL 16



### Health- **Convenciones**:- **Convenciones**:

**Verificar estado del microservicio**

```http  - **DB**: `snake_case`  - **DB**: `snake_case`

GET /health

```  - **API/JSON**: `snake_case`  - **API/JSON**: `camelCase`

**200 OK**

```json

{ "ok": true, "service": "vendedores", "version": "v1" }

```------



---



### Vendedores## 📌 Endpoints## 📌 Endpoints



#### Crear vendedor

```http

POST /vendedores### Health### Health

Content-Type: application/json

```**Verificar estado del microservicio****Verificar estado del microservicio**

**Body**

```json```http```http

{

  "nombre": "Juan",GET /healthGET /health

  "apellidos": "Pérez García",

  "correo": "juan.perez@example.com",``````

  "telefono": "+57 300 123 4567",

  "zona": "Colombia",**200 OK****200 OK**

  "estado": "activo",

  "usuario_creacion": "admin"```json```json

}

```{ "ok": true, "service": "vendedores", "version": "v1" }{ "ok": true, "service": "vendedores", "version": "v1" }

**201 Created** → `Vendedor`

```json``````

{

  "id": "550e8400-e29b-41d4-a716-446655440000",

  "nombre": "Juan",

  "apellidos": "Pérez García",------

  "correo": "juan.perez@example.com",

  "telefono": "+57 300 123 4567",

  "zona": "Colombia",

  "estado": "activo",### Vendedores### Vendedores

  "usuario_creacion": "admin",

  "fecha_creacion": "2025-10-25T10:30:00",

  "fecha_actualizacion": "2025-10-25T10:30:00"

}#### Crear vendedor#### Crear vendedor

```

```http```http

#### Listar vendedores

```httpPOST /vendedoresPOST /vendedores

GET /vendedores?zona={zona}&estado={activo|inactivo}&page={1..n}&size={1..100}

```Content-Type: application/jsonContent-Type: application/json

**200 OK** → `PagedVendedor`

```json``````

{

  "items": [**Body****Body**

    {

      "id": "uuid",```json```json

      "nombre": "Juan",

      "apellidos": "Pérez García",{{

      "correo": "juan.perez@example.com",

      "telefono": "+57 300 123 4567",  "nombre": "Juan",  "nombre": "pr",

      "zona": "Colombia",

      "estado": "activo",  "apellidos": "Pérez García",  "apellidos": "ueba",

      "usuario_creacion": "admin",

      "fecha_creacion": "2025-10-25T10:30:00",  "correo": "juan.perez@example.com",  "correo": "tttt@example.com",

      "fecha_actualizacion": "2025-10-25T10:30:00"

    }  "telefono": "+57 300 123 4567",  "telefono": "32165498798",

  ],

  "total": 1,  "zona": "Colombia",  "zona": "Colombia",

  "page": 1,

  "size": 10,  "estado": "activo",  "telefono": "6012345578"

  "pages": 1

}  "usuario_creacion": "admin"}

```

}

#### Obtener vendedor

```http``````

GET /vendedores/{vendedorId}

```**201 Created** → `Vendedor`**201 Created** → `Vendedor`

**200 OK** → `Vendedor` | **404**

```json

#### Actualizar vendedor (parcial)

```http{#### Listar vendedores

PATCH /vendedores/{vendedorId}

Content-Type: application/json  "id": "550e8400-e29b-41d4-a716-446655440000",```http

```

**Body (ejemplo)**  "nombre": "Juan",GET /vendedores?zona={zona}&estado={activo|inactivo}&page={1..n}&size={1..100}

```json

{  "apellidos": "Pérez García",```

  "nombre": "Ana M. Gomez",

  "zona": "Centro"  "correo": "juan.perez@example.com",**200 OK** → `PagedVendedor`

}

```  "telefono": "+57 300 123 4567",

**200 OK** → `Vendedor` | **400** | **404** | **409**

  "zona": "Colombia",#### Obtener vendedor

#### Asociar cliente a vendedor

```http  "estado": "activo",```http

PATCH /vendedores/clientes

Content-Type: application/json  "usuario_creacion": "admin",GET /vendedores/{vendedorId}

```

**Body**  "fecha_creacion": "2025-10-25T10:30:00",```

```json

{  "fecha_actualizacion": "2025-10-25T10:30:00"**200 OK** → `Vendedor` | **404**

  "vendedor_email": "juan.perez@example.com",

  "cliente_id": "uuid-cliente"}

}

``````#### Actualizar vendedor (parcial)

**200 OK** | **400** | **404**

```http

---

#### Listar vendedoresPATCH /vendedores/{vendedorId}

### Planes de Venta

```httpContent-Type: application/json

#### Crear o actualizar plan (UPSERT)

```httpGET /vendedores?zona={zona}&estado={activo|inactivo}&page={1..n}&size={1..100}```

POST /planes-venta

Content-Type: application/json```**Body (ejemplo)**

```

**Body****200 OK** → `PagedVendedor````json

```json

{```json{ "nombre": "Ana M. Gomez", "zona": "Centro" }

  "nombre_plan": "Plan Q1 2025",

  "gerente_id": "uuid-gerente",{```

  "vendedor_id": "uuid-vendedor",

  "periodo": "2025-01",  "items": [**200 OK** → `Vendedor` | **400** | **404** | **409**

  "meta_ingresos": 50000.00,

  "meta_visitas": 100,    {

  "meta_clientes_nuevos": 20,

  "estado": "activo"      "id": "uuid",---

}

```      "nombre": "Juan",

**201 Created** (nuevo plan) | **200 OK** (actualizado)

```json      "apellidos": "Pérez García",### Planes de Venta

{

  "id": "uuid",      "correo": "juan.perez@example.com",

  "nombre_plan": "Plan Q1 2025",

  "gerente_id": "uuid-gerente",      "telefono": "+57 300 123 4567",#### Upsert plan (vendedorId + periodo)

  "vendedor_id": "uuid-vendedor",

  "periodo": "2025-01",      "zona": "Colombia",```http

  "meta_ingresos": 50000.00,

  "meta_visitas": 100,      "estado": "activo",POST /planes-venta

  "meta_clientes_nuevos": 20,

  "estado": "activo",      "usuario_creacion": "admin",Content-Type: application/json

  "fecha_creacion": "2025-10-25T10:30:00",

  "fecha_actualizacion": "2025-10-25T10:30:00",      "fecha_creacion": "2025-10-25T10:30:00",```

  "operacion": "crear"

}      "fecha_actualizacion": "2025-10-25T10:30:00"**Body**

```

    }```json

**Errores**: **400** | **404** | **409** | **500**

  ],{

#### Obtener plan por ID

```http  "total": 1,  "vendedorId": "<uuid>",

GET /planes-venta/{planId}

```  "page": 1,  "periodo": "YYYY-MM",

**200 OK** → `Plan` | **404**

  "size": 10,  "objetivoMensual": 1500000,

#### Listar planes

```http  "pages": 1  "metaUnidades": 25,

GET /planes-venta?vendedor_id={uuid}&periodo={YYYY-MM}&estado={activo|inactivo}&page={1..n}&size={1..100}

```}  "estado": "activo"

**200 OK** → `PagedPlan`

```json```}

{

  "items": [```

    {

      "id": "uuid",#### Obtener vendedor**201 Created** → `Plan` | **400** | **404** | **409**

      "nombre_plan": "Plan Q1 2025",

      "gerente_id": "uuid-gerente",```http

      "vendedor_id": "uuid-vendedor",

      "periodo": "2025-01",GET /vendedores/{vendedorId}#### Listar planes

      "meta_ingresos": 50000.00,

      "meta_visitas": 100,``````http

      "meta_clientes_nuevos": 20,

      "estado": "activo",**200 OK** → `Vendedor` | **404**GET /planes-venta?vendedorId={uuid}&periodo={YYYY-MM}&page={1..n}&size={1..100}

      "fecha_creacion": "2025-10-25T10:30:00",

      "fecha_actualizacion": "2025-10-25T10:30:00"```

    }

  ],#### Actualizar vendedor (parcial)**200 OK** → `PagedPlan`

  "total": 1,

  "page": 1,```http

  "size": 10,

  "pages": 1PATCH /vendedores/{vendedorId}---

}

```Content-Type: application/json



---```### Asignaciones de Zona



## 🧱 Modelos de Datos (DB)**Body (ejemplo)**



> **Convención**: tablas/columnas en `snake_case`.```json#### Crear asignación



### `vendedores`{```http

| Columna              | Tipo           | Reglas                         |

|---                   |---             |---                             |  "nombre": "Ana M. Gomez",POST /vendedores/{vendedorId}/asignaciones

| `id`                 | string(36)     | PK, UUID                       |

| `nombre`             | string(150)    | Requerido                      |  "zona": "Centro"Content-Type: application/json

| `apellidos`          | string(150)    | Requerido                      |

| `correo`             | string(255)    | **Unique**, requerido, indexed |}```

| `telefono`           | string(20)     | Opcional                       |

| `zona`               | string(80)     | Opcional                       |```**Body**

| `estado`             | string(20)     | `activo`/`inactivo`, default `activo` |

| `usuario_creacion`   | string(100)    | Opcional                       |**200 OK** → `Vendedor` | **400** | **404** | **409**```json

| `fecha_creacion`     | timestamp      | default now()                  |

| `usuario_actualizacion` | string(100) | Opcional                       |{ "zona": "Occidente", "vigenteDesde": "YYYY-MM-DD", "vigenteHasta": null, "activa": true }

| `fecha_actualizacion`| timestamp      | auto on update                 |

#### Asociar cliente a vendedor```

### `planes_venta`

| Columna                | Tipo            | Reglas                                   |```http**201 Created** → `Asignacion` | **400** | **404**

|---                     |---              |---                                       |

| `id`                   | string(36)      | PK, UUID                                 |PATCH /vendedores/clientes

| `nombre_plan`          | string(200)     | Requerido                                |

| `gerente_id`           | string(36)      | Requerido                                |Content-Type: application/json#### Listar asignaciones

| `vendedor_id`          | string(36)      | FK → `vendedores(id)`, CASCADE           |

| `periodo`              | string(7)       | `YYYY-MM`, requerido                     |``````http

| `meta_ingresos`        | numeric(14,2)   | Requerido                                |

| `meta_visitas`         | integer         | Requerido                                |**Body**GET /asignaciones?vendedorId={uuid}&zona={zona}&activas={true|false}&page={1..n}&size={1..100}

| `meta_clientes_nuevos` | integer         | Requerido                                |

| `estado`               | string(20)      | `activo`/`inactivo`, default `activo`    |```json```

| `fecha_creacion`       | timestamp       | default now()                            |

| `fecha_actualizacion`  | timestamp       | auto on update                           |{**200 OK** → `PagedAsignacion`



**Unique:** (`vendedor_id`, `periodo`)  "vendedor_email": "juan.perez@example.com",



### `asignaciones_zona`  "cliente_id": "uuid-cliente"#### Cerrar asignación

| Columna         | Tipo        | Reglas                             |

|---              |---          |---                                 |}```http

| `id`            | string(36)  | PK, UUID                           |

| `vendedor_id`   | string(36)  | FK → `vendedores(id)`, CASCADE     |```PATCH /asignaciones/{asignacionId}/cerrar

| `zona`          | string(80)  | Requerido                          |

| `vigente_desde` | date        | Requerido                          |**200 OK** | **400** | **404**Content-Type: application/json

| `vigente_hasta` | date\|null  | Opcional                           |

| `activa`        | boolean     | default true                       |```



------**Body (opcional)**



## 🧪 Validaciones```json



**Vendedores**### Planes de Venta{ "vigenteHasta": "YYYY-MM-DD" }

- `nombre`: requerido, máx 150 caracteres

- `apellidos`: requerido, máx 150 caracteres```

- `correo`: requerido, único, máx 255 caracteres, formato email válido

- `telefono`: opcional, máx 20 caracteres#### Crear o actualizar plan (UPSERT)**200 OK** → `Asignacion` | **404**

- `zona`: opcional, máx 80 caracteres

- `estado`: `activo` | `inactivo````http

- Paginación: `page ≥ 1`, `1 ≤ size ≤ 100`

POST /planes-venta---

**Planes de Venta**

- `nombre_plan`: requerido, máx 200 caracteresContent-Type: application/json

- `gerente_id`: UUID válido, requerido

- `vendedor_id`: UUID válido y existente en tabla vendedores```## 🧱 Modelos de Datos (DB)

- `periodo`: regex `^\d{4}-(0[1-9]|1[0-2])$` (formato YYYY-MM)

- `meta_ingresos`: decimal ≥ 0**Body**

- `meta_visitas`: entero ≥ 0

- `meta_clientes_nuevos`: entero ≥ 0```json> **Convención**: tablas/columnas en `snake_case`.

- `estado`: `activo` | `inactivo`

- UPSERT basado en unique constraint `(vendedor_id, periodo)`{



**Asignaciones**  "nombre_plan": "Plan Q1 2025",### `vendedores`

- `zona`: requerido, máx 80 caracteres

- `vigente_desde`: formato `YYYY-MM-DD`  "gerente_id": "uuid-gerente",| Columna              | Tipo           | Reglas                         |

- `vigente_hasta`: formato `YYYY-MM-DD` o null

- `activa`: boolean  "vendedor_id": "uuid-vendedor",|---                   |---             |---                             |



---  "periodo": "2025-01",| `id`                 | uuid/string    | PK                             |



## ❌ Errores  "meta_ingresos": 50000.00,| `identificacion`     | string(30)     | **Unique**, requerido          |



| HTTP | Código              | Mensaje (ejemplos)                                        |  "meta_visitas": 100,| `nombre`             | string(150)    | Requerido                      |

|------|---------------------|-----------------------------------------------------------|

| 400  | `VALIDATION_ERROR`  | Campos faltantes, tipos inválidos, formato `periodo` mal formado, valores negativos |  "meta_clientes_nuevos": 20,| `zona`               | string(80)     | Opcional                       |

| 404  | `NOT_FOUND`         | `vendedor no encontrado`, `plan no encontrado`            |

| 409  | `CONFLICT`          | `correo ya registrado`, `plan duplicado para vendedor y periodo` |  "estado": "activo"| `estado`             | string(20)     | `activo`/`inactivo`            |

| 500  | `INTERNAL_ERROR`    | `Error interno del servidor`                              |

}| `fecha_creacion`     | timestamp      | default now()                  |

**Payload de error**

```json```| `fecha_actualizacion`| timestamp      | auto on update                 |

{

  "error": "mensaje legible",**201 Created** (nuevo plan) | **200 OK** (actualizado)

  "codigo": "CODIGO_INTERNO"

}```json### `planes_venta`

```

{| Columna             | Tipo            | Reglas                                   |

---

  "id": "uuid",|---                  |---              |---                                       |

## 🧰 Ejemplos (cURL)

  "nombre_plan": "Plan Q1 2025",| `id`                | uuid/string     | PK                                       |

```bash

# Health check  "gerente_id": "uuid-gerente",| `vendedor_id`       | uuid/string     | FK → `vendedores(id)`                    |

curl http://localhost:5007/health

  "vendedor_id": "uuid-vendedor",| `periodo`           | char(7)         | `YYYY-MM`, requerido                     |

# Crear vendedor

curl -X POST http://localhost:5007/vendedores \  "periodo": "2025-01",| `objetivo_mensual`  | numeric(14,2)   | > 0, requerido                           |

  -H "Content-Type: application/json" \

  -d '{  "meta_ingresos": 50000.00,| `meta_unidades`     | int             | Opcional                                 |

    "nombre": "Juan",

    "apellidos": "Pérez García",  "meta_visitas": 100,| `estado`            | string(20)      | `activo`/`inactivo`                      |

    "correo": "juan.perez@example.com",

    "telefono": "+57 300 123 4567",  "meta_clientes_nuevos": 20,| `fecha_creacion`    | timestamp       | default now()                            |

    "zona": "Colombia",

    "estado": "activo"  "estado": "activo",| `fecha_actualizacion`| timestamp      | auto on update                           |

  }'

  "fecha_creacion": "2025-10-25T10:30:00",**Unique:** (`vendedor_id`, `periodo`)

# Listar vendedores

curl "http://localhost:5007/vendedores?zona=Colombia&estado=activo&page=1&size=10"  "fecha_actualizacion": "2025-10-25T10:30:00",



# Crear plan de venta (UPSERT)  "operacion": "crear"### `asignaciones_zona`

curl -X POST http://localhost:5007/planes-venta \

  -H "Content-Type: application/json" \}| Columna         | Tipo        | Reglas                             |

  -d '{

    "nombre_plan": "Plan Q1 2025",```|---              |---          |---                                 |

    "gerente_id": "uuid-gerente",

    "vendedor_id": "uuid-vendedor",| `id`            | uuid/string | PK                                 |

    "periodo": "2025-01",

    "meta_ingresos": 50000.00,**Errores**: **400** | **404** | **409** | **500**| `vendedor_id`   | uuid/string | FK → `vendedores(id)`              |

    "meta_visitas": 100,

    "meta_clientes_nuevos": 20,| `zona`          | string(80)  | Requerido                          |

    "estado": "activo"

  }'#### Obtener plan por ID| `vigente_desde` | date        | Requerido                          |



# Listar planes de venta```http| `vigente_hasta` | date|null   | Opcional                           |

curl "http://localhost:5007/planes-venta?vendedor_id=uuid&periodo=2025-01&page=1&size=10"

GET /planes-venta/{planId}| `activa`        | boolean     | default true                       |

# Obtener plan específico

curl http://localhost:5007/planes-venta/{planId}```



# Asociar cliente a vendedor**200 OK** → `Plan` | **404**---

curl -X PATCH http://localhost:5007/vendedores/clientes \

  -H "Content-Type: application/json" \

  -d '{

    "vendedor_email": "juan.perez@example.com",#### Listar planes## 🧪 Validaciones

    "cliente_id": "uuid-cliente"

  }'```http**Vendedores**

```

GET /planes-venta?vendedor_id={uuid}&periodo={YYYY-MM}&estado={activo|inactivo}&page={1..n}&size={1..100}- `identificacion`: requerida, única, máx 30.

---

```- `nombre`: requerido, máx 150.

## 📊 Métricas & Observabilidad

- **Health**: `GET /health`**200 OK** → `PagedPlan`- `estado`: `activo` | `inactivo`.

- **Trazas/Métricas sugeridas**:

  - Latencia p95 por endpoint```json- Listado: `page ≥ 1`, `1 ≤ size ≤ 100`.

  - Tasa 4xx/5xx

  - Conteo de operaciones UPSERT (crear vs actualizar){

  - Tasa de conflictos en planes de venta

- **Logs**: JSON con `vendedor_id`, `plan_id`, `trace_id` (si aplica)  "items": [**Planes**



---    {- `vendedorId`: UUID válido y existente.



## 🚀 Despliegue      "id": "uuid",- `periodo`: regex `^\d{4}-(0[1-9]|1[0-2])$`.

- **Contenedor**: expone puerto `5007`

- **Vars de entorno**:       "nombre_plan": "Plan Q1 2025",- `objetivoMensual`: numérico > 0.

  - `DB_URL`: URL de conexión a PostgreSQL

  - `SERVICE_PORT`: Puerto del servicio (default: 5007)      "gerente_id": "uuid-gerente",- Upsert por `(vendedorId, periodo)`.

  - `APP_ENV`: Ambiente (development/production)

- **Compose**: servicio `postgres` + `vendedores-service`      "vendedor_id": "uuid-vendedor",

- **Migraciones**: Flask-Migrate (`flask db upgrade` al arrancar)

      "periodo": "2025-01",**Asignaciones**

---

      "meta_ingresos": 50000.00,- `zona`: requerido.

## 🔐 Convenciones

- **DB**: `snake_case` (tablas/columnas)      "meta_visitas": 100,- `vigenteDesde`: `YYYY-MM-DD`.

- **Clases Python**: `PascalCase`

- **API/JSON**: `snake_case`      "meta_clientes_nuevos": 20,- `activas` (query): boolean (`true/false/1/0`).

- **Rutas**: minúsculas y plurales (`/vendedores`, `/planes-venta`)

      "estado": "activo",

---

      "fecha_creacion": "2025-10-25T10:30:00",---

## 🗓️ Changelog

      "fecha_actualizacion": "2025-10-25T10:30:00"

### v1.1.0 — 2025-10-25

- **[KAN-86]** Implementado servicio de Planes de Venta con UPSERT    }## ❌ Errores

  - Modelo `PlanVenta` con campos: nombre_plan, gerente_id, vendedor_id, periodo, metas (ingresos, visitas, clientes nuevos)

  - Endpoints: POST (UPSERT), GET por ID, GET lista con filtros  ],| HTTP | Código (interno opcional) | Mensaje (ejemplos)                              |

  - Validaciones: periodo (YYYY-MM), valores no negativos, vendedor existente

  - Unique constraint en (vendedor_id, periodo)  "total": 1,|---|---|---|

- Actualizado contrato para reflejar estructura actual de campos

- Endpoint de asociación de cliente a vendedor documentado  "page": 1,| 400 | `VALIDATION_ERROR` | Faltan campos, tipos inválidos, `periodo` mal formado |



### v1.0.0 — 2025-10-10  "size": 10,| 404 | `NOT_FOUND`        | `vendedor no encontrado`, `asignación no encontrada` |

- Primera versión del servicio

- CRUD de vendedores  "pages": 1| 409 | `CONFLICT`         | `identificacion ya registrada`, plan duplicado       |

- Modelo de asignaciones de zona

}| 500 | `INTERNAL_ERROR`   | `internal_error`                                     |

---

```

## 👥 Contacto / Ownership

- **Equipo**: Proyecto MediSupply**Payload de error (recomendado)**

- **Repositorio**: MediSupply-backend

- **Branch**: KAN-86-Crear-plan-de-venta---```json


{ "error": "mensaje legible", "codigo": "CODIGO_INTERNO_OPCIONAL" }

## 🧱 Modelos de Datos (DB)```



> **Convención**: tablas/columnas en `snake_case`.---



### `vendedores`## 🧰 Ejemplos (cURL / Insomnia)

| Columna              | Tipo           | Reglas                         |```bash

|---                   |---             |---                             |# Health

| `id`                 | string(36)     | PK, UUID                       |curl http://localhost:8001/v1/health

| `nombre`             | string(150)    | Requerido                      |

| `apellidos`          | string(150)    | Requerido                      |# Crear vendedor

| `correo`             | string(255)    | **Unique**, requerido, indexed |curl -X POST http://localhost:8001/v1/vendedores -H "Content-Type: application/json"   -d '{"identificacion":"CC123","nombre":"Ana Gomez","zona":"Norte","estado":"activo"}'

| `telefono`           | string(20)     | Opcional                       |

| `zona`               | string(80)     | Opcional                       |# Upsert plan

| `estado`             | string(20)     | `activo`/`inactivo`, default `activo` |curl -X POST http://localhost:8001/v1/planes-venta -H "Content-Type: application/json"   -d '{"vendedorId":"<uuid>","periodo":"2025-10","objetivoMensual":1500000}'

| `usuario_creacion`   | string(100)    | Opcional                       |```

| `fecha_creacion`     | timestamp      | default now()                  |

| `usuario_actualizacion` | string(100) | Opcional                       |---

| `fecha_actualizacion`| timestamp      | auto on update                 |

## 📊 Métricas & Observabilidad

### `planes_venta`- **Health**: `GET /health`

| Columna                | Tipo            | Reglas                                   |- **Trazas/Métricas sugeridas**:

|---                     |---              |---                                       |  - Latencia p95 por endpoint

| `id`                   | string(36)      | PK, UUID                                 |  - Tasa 4xx/5xx

| `nombre_plan`          | string(200)     | Requerido                                |  - Conteo de upserts de plan

| `gerente_id`           | string(36)      | Requerido                                |- **Logs**: JSON con `vendedorId`, `asignacionId`, `trace_id` (si aplica)

| `vendedor_id`          | string(36)      | FK → `vendedores(id)`, CASCADE           |

| `periodo`              | string(7)       | `YYYY-MM`, requerido                     |---

| `meta_ingresos`        | numeric(14,2)   | Requerido                                |

| `meta_visitas`         | integer         | Requerido                                |## 🚀 Despliegue

| `meta_clientes_nuevos` | integer         | Requerido                                |- **Contenedor**: expone puerto `8001`

| `estado`               | string(20)      | `activo`/`inactivo`, default `activo`    |- **Vars**: `DB_URL`, `SERVICE_PORT`, `APP_ENV`

| `fecha_creacion`       | timestamp       | default now()                            |- **Compose**: servicio `postgres` + `vendedores-service`

| `fecha_actualizacion`  | timestamp       | auto on update                           |- **Migraciones**: Alembic/Flask-Migrate (`flask db upgrade` al arrancar)



**Unique:** (`vendedor_id`, `periodo`)---



### `asignaciones_zona`## 🔐 Convenciones

| Columna         | Tipo        | Reglas                             |- **DB**: `snake_case` (tablas/columnas)

|---              |---          |---                                 |- **Clases Python**: `CamelCase`

| `id`            | string(36)  | PK, UUID                           |- **API/JSON**: `camelCase`

| `vendedor_id`   | string(36)  | FK → `vendedores(id)`, CASCADE     |- **Rutas**: minúsculas y plurales (ej. `/vendedores`, `/planes-venta`)

| `zona`          | string(80)  | Requerido                          |

| `vigente_desde` | date        | Requerido                          |---

| `vigente_hasta` | date|null   | Opcional                           |

| `activa`        | boolean     | default true                       |## 🗓️ Changelog

- **v1.0.0** — Primera versión del servicio y contrato (2025-10-10T03:04:58Z).

---

---

## 🧪 Validaciones

## 👥 Contacto / Ownership

**Vendedores**- **Equipo**: _TODO_

- `nombre`: requerido, máx 150 caracteres- **Canal**: _TODO_

- `apellidos`: requerido, máx 150 caracteres- **Owner técnico**: _TODO_
- `correo`: requerido, único, máx 255 caracteres, formato email válido
- `telefono`: opcional, máx 20 caracteres
- `zona`: opcional, máx 80 caracteres
- `estado`: `activo` | `inactivo`
- Paginación: `page ≥ 1`, `1 ≤ size ≤ 100`

**Planes de Venta**
- `nombre_plan`: requerido, máx 200 caracteres
- `gerente_id`: UUID válido, requerido
- `vendedor_id`: UUID válido y existente en tabla vendedores
- `periodo`: regex `^\d{4}-(0[1-9]|1[0-2])$` (formato YYYY-MM)
- `meta_ingresos`: decimal ≥ 0
- `meta_visitas`: entero ≥ 0
- `meta_clientes_nuevos`: entero ≥ 0
- `estado`: `activo` | `inactivo`
- UPSERT basado en unique constraint `(vendedor_id, periodo)`

**Asignaciones**
- `zona`: requerido, máx 80 caracteres
- `vigente_desde`: formato `YYYY-MM-DD`
- `vigente_hasta`: formato `YYYY-MM-DD` o null
- `activa`: boolean

---

## ❌ Errores

| HTTP | Código              | Mensaje (ejemplos)                                        |
|------|---------------------|-----------------------------------------------------------|
| 400  | `VALIDATION_ERROR`  | Campos faltantes, tipos inválidos, formato `periodo` mal formado, valores negativos |
| 404  | `NOT_FOUND`         | `vendedor no encontrado`, `plan no encontrado`            |
| 409  | `CONFLICT`          | `correo ya registrado`, `plan duplicado para vendedor y periodo` |
| 500  | `INTERNAL_ERROR`    | `Error interno del servidor`                              |

**Payload de error**
```json
{
  "error": "mensaje legible",
  "codigo": "CODIGO_INTERNO"
}
```

---

## 🧰 Ejemplos (cURL)

```bash
# Health check
curl http://localhost:5007/health

# Crear vendedor
curl -X POST http://localhost:5007/vendedores \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellidos": "Pérez García",
    "correo": "juan.perez@example.com",
    "telefono": "+57 300 123 4567",
    "zona": "Colombia",
    "estado": "activo"
  }'

# Listar vendedores
curl "http://localhost:5007/vendedores?zona=Colombia&estado=activo&page=1&size=10"

# Crear plan de venta (UPSERT)
curl -X POST http://localhost:5007/planes-venta \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_plan": "Plan Q1 2025",
    "gerente_id": "uuid-gerente",
    "vendedor_id": "uuid-vendedor",
    "periodo": "2025-01",
    "meta_ingresos": 50000.00,
    "meta_visitas": 100,
    "meta_clientes_nuevos": 20,
    "estado": "activo"
  }'

# Listar planes de venta
curl "http://localhost:5007/planes-venta?vendedor_id=uuid&periodo=2025-01&page=1&size=10"

# Obtener plan específico
curl http://localhost:5007/planes-venta/{planId}

# Asociar cliente a vendedor
curl -X PATCH http://localhost:5007/vendedores/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "vendedor_email": "juan.perez@example.com",
    "cliente_id": "uuid-cliente"
  }'
```

---

## 📊 Métricas & Observabilidad
- **Health**: `GET /health`
- **Trazas/Métricas sugeridas**:
  - Latencia p95 por endpoint
  - Tasa 4xx/5xx
  - Conteo de operaciones UPSERT (crear vs actualizar)
  - Tasa de conflictos en planes de venta
- **Logs**: JSON con `vendedor_id`, `plan_id`, `trace_id` (si aplica)

---

## 🚀 Despliegue
- **Contenedor**: expone puerto `5007`
- **Vars de entorno**: 
  - `DB_URL`: URL de conexión a PostgreSQL
  - `SERVICE_PORT`: Puerto del servicio (default: 5007)
  - `APP_ENV`: Ambiente (development/production)
- **Compose**: servicio `postgres` + `vendedores-service`
- **Migraciones**: Flask-Migrate (`flask db upgrade` al arrancar)

---

## 🔐 Convenciones
- **DB**: `snake_case` (tablas/columnas)
- **Clases Python**: `PascalCase`
- **API/JSON**: `snake_case`
- **Rutas**: minúsculas y plurales (`/vendedores`, `/planes-venta`)

---

## 🗓️ Changelog

### v1.1.0 — 2025-10-25
- **[KAN-86]** Implementado servicio de Planes de Venta con UPSERT
  - Modelo `PlanVenta` con campos: nombre_plan, gerente_id, vendedor_id, periodo, metas (ingresos, visitas, clientes nuevos)
  - Endpoints: POST (UPSERT), GET por ID, GET lista con filtros
  - Validaciones: periodo (YYYY-MM), valores no negativos, vendedor existente
  - Unique constraint en (vendedor_id, periodo)
- Actualizado contrato para reflejar estructura actual de campos
- Endpoint de asociación de cliente a vendedor documentado

### v1.0.0 — 2025-10-10
- Primera versión del servicio
- CRUD de vendedores
- Modelo de asignaciones de zona

---

## 👥 Contacto / Ownership
- **Equipo**: Proyecto MediSupply
- **Repositorio**: MediSupply-backend
- **Branch**: KAN-86-Crear-plan-de-venta
