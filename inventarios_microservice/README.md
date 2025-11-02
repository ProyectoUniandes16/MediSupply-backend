# Microservicio de Inventarios

Microservicio para la gestión de inventarios de productos en MediSupply.

## Características

- ✅ CRUD completo de inventarios
- ✅ Validaciones de datos robustas
- ✅ Manejo de errores personalizado
- ✅ Ajuste de cantidades (incremento/decremento)
- ✅ Filtrado por producto y ubicación
- ✅ Paginación de resultados
- ✅ Auditoría de cambios (usuario y fecha)
- ✅ Docker Compose para desarrollo

## Tecnologías

- Python 3.11
- Flask
- SQLAlchemy
- PostgreSQL 15
- Docker & Docker Compose

## Instalación y Ejecución

### Con Docker Compose (Recomendado)

```bash
# Construir e iniciar los servicios
docker-compose up --build

# Detener los servicios
docker-compose down

# Detener y eliminar volúmenes (limpia la BD)
docker-compose down -v
```

El servicio estará disponible en: `http://localhost:5009`

### Sin Docker (Desarrollo local)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Ejecutar el servicio
python run.py
```

## API Endpoints

### Health Check
```
GET /health
```

### Crear Inventario
```
POST /api/inventarios
Content-Type: application/json

{
  "productoId": "PROD-001",
  "cantidad": 100,
  "ubicacion": "Bodega A - Estante 1",
  "usuario": "admin"
}
```

### Listar Inventarios
```
GET /api/inventarios?productoId=PROD-001&ubicacion=Bodega&limite=50&offset=0
```

### Obtener Inventario por ID
```
GET /api/inventarios/{inventario_id}
```

### Actualizar Inventario
```
PUT /api/inventarios/{inventario_id}
Content-Type: application/json

{
  "cantidad": 150,
  "ubicacion": "Bodega B - Estante 2",
  "usuario": "admin"
}
```

### Eliminar Inventario
```
DELETE /api/inventarios/{inventario_id}
```

### Ajustar Cantidad
```
POST /api/inventarios/{inventario_id}/ajustar
Content-Type: application/json

{
  "ajuste": -10,  // Negativo para decrementar, positivo para incrementar
  "usuario": "admin"
}
```

### Obtener Inventarios por Producto
```
GET /api/inventarios/producto/{producto_id}
```

## Validaciones

- `productoId`: Obligatorio, 1-100 caracteres
- `cantidad`: Obligatorio, entero positivo
- `ubicacion`: Obligatorio, 1-100 caracteres
- No se permite duplicar producto + ubicación
- Los ajustes no pueden resultar en cantidades negativas

## Códigos de Respuesta

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Error de validación
- `404 Not Found`: Recurso no encontrado
- `409 Conflict`: Conflicto (duplicado)
- `500 Internal Server Error`: Error del servidor

## Estructura del Proyecto

```
inventarios_microservice/
├── app/
│   ├── __init__.py           # Factory pattern de Flask
│   ├── models/
│   │   ├── __init__.py       # Inicialización de SQLAlchemy
│   │   └── inventario.py     # Modelo de datos
│   ├── routes/
│   │   ├── health.py         # Health check
│   │   ├── inventarios.py    # Endpoints del CRUD
│   │   └── errors.py         # Manejadores de errores
│   ├── services/
│   │   ├── __init__.py       # Exportación de errores
│   │   └── inventarios_service.py  # Lógica de negocio
│   └── utils/
│       ├── errors.py         # Definición de excepciones
│       └── validators.py     # Funciones de validación
├── test/                     # Tests unitarios
├── docker-compose.yml        # Orquestación de contenedores
├── Dockerfile               # Imagen del servicio
├── requirements.txt         # Dependencias Python
├── .env.example            # Ejemplo de configuración
└── run.py                  # Punto de entrada
```

## Pruebas con cURL

### Crear un inventario
```bash
curl -X POST http://localhost:5009/api/inventarios \
  -H "Content-Type: application/json" \
  -d '{
    "productoId": "PROD-001",
    "cantidad": 100,
    "ubicacion": "Bodega A",
    "usuario": "admin"
  }'
```

### Listar inventarios
```bash
curl http://localhost:5009/api/inventarios
```

### Obtener inventario específico
```bash
curl http://localhost:5009/api/inventarios/{id}
```

### Actualizar inventario
```bash
curl -X PUT http://localhost:5009/api/inventarios/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "cantidad": 150,
    "usuario": "admin"
  }'
```

### Ajustar cantidad
```bash
curl -X POST http://localhost:5009/api/inventarios/{id}/ajustar \
  -H "Content-Type: application/json" \
  -d '{
    "ajuste": -10,
    "usuario": "admin"
  }'
```

### Eliminar inventario
```bash
curl -X DELETE http://localhost:5009/api/inventarios/{id}
```

## Tests

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
```

## Logs y Debugging

Para habilitar logs de SQL:
```bash
export SQLALCHEMY_ECHO=True
```

## Autor

Proyecto Final - MediSupply Backend
