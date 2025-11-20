# Microservicio de Productos - MediSupply

Microservicio encargado de la gestión de productos médicos para el sistema MediSupply. Permite el registro de productos con todas sus especificaciones y certificaciones sanitarias.

## 🚀 Funcionalidades

### ✅ Implementadas (HU KAN-96)

- **Carga de Producto**: Registro completo de productos con validación de datos
- **Gestión de Certificaciones**: Upload y almacenamiento de certificaciones sanitarias (INVIMA, FDA, EMA)
- **Validación de SKU**: Verificación de unicidad y formato correcto del código SKU
- **Categorías Fijas**: medicamento, insumo, reactivo, dispositivo
- **Estados de Producto**: Gestión de estados Activo/Inactivo
- **Auditoría**: Registro de usuario, fecha y hora de creación
- **Health Check**: Endpoint para verificar el estado del servicio

## 🛠️ Tecnologías

- **Framework**: Flask 2.3.3
- **Base de Datos**: PostgreSQL (desarrollo) / SQLite (testing)
- **ORM**: SQLAlchemy 2.0.21
- **Validación**: Validadores customizados
- **Testing**: pytest con coverage
- **Upload**: Werkzeug para manejo seguro de archivos
- **Procesamiento asíncrono**: Redis (pub/sub) + worker local

## 📋 Requisitos

- Python 3.10+
- PostgreSQL 12+ (para desarrollo)
- pip / pipenv / poetry

## 🏃‍♂️ Ejecución Local

### 1. Instalar dependencias

```bash
cd productos_microservice
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env`:

```properties
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/medisupply
SECRET_KEY=supersecretkey
FLASK_DEBUG=true
```

### 3. Ejecutar el microservicio

```bash
python run.py
```

El servidor estará disponible en:
- http://localhost:5008

### 4. Ejecutar worker de importación asíncrona

El worker escucha el canal Redis `productos_import_csv` y procesa los CSV guardados en `local_imports/`:

```bash
python app/workers/sqs_worker.py
```

> Asegúrate de que `redis_service` esté corriendo (por docker-compose o localmente) y que el contenedor del worker comparta el directorio `local_imports/` con la app.

## 🧪 Ejecutar Tests

```bash
# Tests completos con coverage
python -m pytest tests/ -v

# Con reporte HTML
python -m pytest tests/ --cov=app --cov-report=html
```

## 🐳 Ejecutar con Docker

### 1. Construir la imagen

```bash
docker build -t productos-microservice .
```

### 2. Ejecutar el contenedor

```bash
# Con variables de entorno inline
docker run -p 5008:5008 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5433/medisupply \
  -e SECRET_KEY=supersecretkey \
  -e FLASK_DEBUG=false \
  productos-microservice

# O con archivo .env
docker run -p 5008:5008 --env-file .env productos-microservice
```

### 3. Verificar

```bash
curl http://localhost:5008/api/productos/health
```

**Nota**: Usar `host.docker.internal` para conectar con PostgreSQL en el host desde el contenedor.

## 📁 Estructura del Proyecto

```
productos_microservice/
├── app/
│   ├── __init__.py              # Factory Flask
│   ├── config.py                # Configuraciones
│   ├── extensions.py            # SQLAlchemy + Marshmallow
│   ├── models/
│   │   └── producto.py          # Producto + CertificacionProducto
│   ├── routes/
│   │   └── productos_bp.py      # Endpoints REST
│   ├── services/
│   │   └── producto_service.py  # Lógica de negocio
│   └── utils/
│       └── validators.py        # Validadores
├── tests/                       # Suite de tests
├── requirements.txt             # Dependencias
├── run.py                      # Punto de entrada
└── README.md                   # Este archivo
```

## 🔄 Importación Masiva (CSV)

- Los archivos CSV se almacenan en `local_imports/` inmediatamente después del upload.
- Se publica un mensaje en Redis vía `redis_service` (`POST /api/queue/publish`) con los datos del job.
- El worker (`app/workers/sqs_worker.py`) consume el canal `productos_import_csv`, lee el archivo local y ejecuta `CSVProductoService`.
- El progreso y los errores se registran en la tabla `import_jobs`.

### Variables relevantes

- `REDIS_SERVICE_URL`: URL HTTP del microservicio Redis (por defecto `http://localhost:5011`).
- `REDIS_IMPORT_CHANNEL`: Canal pub/sub utilizado para importaciones (por defecto `productos_import_csv`).

## 🚦 Health Check

```bash
curl http://localhost:5008/api/productos/health
```

## 📊 Categorías de Productos

- `medicamento`: Medicamentos y fármacos
- `insumo`: Insumos médicos
- `reactivo`: Reactivos de laboratorio
- `dispositivo`: Dispositivos médicos

## 🔐 Certificaciones Permitidas

- `INVIMA`: Instituto Nacional de Vigilancia de Medicamentos y Alimentos
- `FDA`: Food and Drug Administration
- `EMA`: European Medicines Agency

## 📝 Validaciones

- **SKU**: Único, 3-50 caracteres alfanuméricos
- **Categoría**: Debe ser una de las 4 categorías fijas
- **Precio**: Debe ser mayor a 0 (USD)
- **Fechas**: Formato DD/MM/YYYY
- **Certificación**: Obligatoria, formatos PDF/JPG/PNG, máximo 5MB

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](../LICENSE).
