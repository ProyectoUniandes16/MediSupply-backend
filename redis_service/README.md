# Redis Service - Microservicio de Cache y Cola

Microservicio dedicado para manejar operaciones de **Cache** y **Cola (Pub/Sub)** usando Redis.

**Puerto:** `5011`

## 🏗️ Arquitectura

```
redis_service (Puerto 5011)
├── Redis Container (Puerto 6379)
├── Cache API (/api/cache)
└── Queue API (/api/queue)
```

## 🚀 Inicio Rápido

### 1. Configuración

```bash
cd redis_service
cp .env.example .env
```

### 2. Levantar con Docker Compose

Desde el directorio raíz:

```bash
docker-compose up redis redis_service
```

### 3. Verificar funcionamiento

```bash
curl http://localhost:5011/health
```

## 📡 Endpoints Disponibles

### Health & Stats

#### GET /health
Health check del servicio

```bash
curl http://localhost:5011/health
```

**Respuesta:**
```json
{
  "service": "redis_service",
  "status": "healthy",
  "port": 5011,
  "redis": "connected"
}
```

#### GET /stats
Estadísticas del servidor Redis

```bash
curl http://localhost:5011/stats
```

---

### Cache API (`/api/cache`)

#### GET /api/cache/{key}
Obtener valor del cache

```bash
curl http://localhost:5011/api/cache/inventarios:producto:123
```

**Respuesta:**
```json
{
  "key": "inventarios:producto:123",
  "value": [...],
  "ttl": 3456
}
```

#### POST /api/cache/
Guardar valor en cache

```bash
curl -X POST http://localhost:5011/api/cache/ \
  -H "Content-Type: application/json" \
  -d '{
    "key": "inventarios:producto:123",
    "value": [{"id": 1, "cantidad": 50}],
    "ttl": 3600
  }'
```

**Respuesta:**
```json
{
  "message": "Valor guardado en cache",
  "key": "inventarios:producto:123",
  "ttl": 3600
}
```

#### DELETE /api/cache/{key}
Eliminar clave del cache

```bash
curl -X DELETE http://localhost:5011/api/cache/inventarios:producto:123
```

#### DELETE /api/cache/pattern/{pattern}
Eliminar claves por patrón

```bash
curl -X DELETE http://localhost:5011/api/cache/pattern/inventarios:*
```

**Respuesta:**
```json
{
  "message": "Claves eliminadas",
  "pattern": "inventarios:*",
  "deleted_count": 15
}
```

#### GET /api/cache/exists/{key}
Verificar si existe una clave

```bash
curl http://localhost:5011/api/cache/exists/inventarios:producto:123
```

#### GET /api/cache/keys?pattern=*
Listar claves por patrón

```bash
curl "http://localhost:5011/api/cache/keys?pattern=inventarios:*"
```

**Respuesta:**
```json
{
  "pattern": "inventarios:*",
  "count": 10,
  "keys": [
    "inventarios:producto:123",
    "inventarios:producto:456"
  ]
}
```

#### POST /api/cache/flush
Limpiar todo el cache (requiere confirmación)

```bash
curl -X POST http://localhost:5011/api/cache/flush \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

---

### Queue API (`/api/queue`) - Pub/Sub

#### POST /api/queue/publish
Publicar mensaje en un canal

```bash
curl -X POST http://localhost:5011/api/queue/publish \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "inventarios_updates",
    "message": {
      "event": "update",
      "producto_id": 123,
      "data": {
        "cantidad": 50,
        "ubicacion": "A1"
      }
    }
  }'
```

**Respuesta:**
```json
{
  "message": "Mensaje publicado",
  "channel": "inventarios_updates",
  "subscribers": 2
}
```

#### GET /api/queue/channels?pattern=*
Listar canales activos

```bash
curl "http://localhost:5011/api/queue/channels?pattern=inventarios*"
```

**Respuesta:**
```json
{
  "pattern": "inventarios*",
  "count": 2,
  "channels": [
    {
      "channel": "inventarios_updates",
      "subscribers": 2
    },
    {
      "channel": "inventarios_deletes",
      "subscribers": 1
    }
  ]
}
```

#### GET /api/queue/subscribers/{channel}
Obtener número de subscriptores

```bash
curl http://localhost:5011/api/queue/subscribers/inventarios_updates
```

**Respuesta:**
```json
{
  "channel": "inventarios_updates",
  "subscribers": 2
}
```

## 🔧 Integración con otros Microservicios

### Desde inventarios_microservice

```python
import requests

# Publicar evento cuando se actualiza inventario
def publicar_actualizacion(producto_id, inventario_data):
    response = requests.post('http://redis_service:5011/api/queue/publish', json={
        'channel': 'inventarios_updates',
        'message': {
            'event': 'update',
            'producto_id': producto_id,
            'data': inventario_data
        }
    })
    return response.json()
```

### Desde producto-inventario-web (BFF)

```python
import requests

# Leer desde cache
def obtener_inventarios_cache(producto_id):
    response = requests.get(
        f'http://redis_service:5011/api/cache/inventarios:producto:{producto_id}'
    )
    
    if response.status_code == 200:
        return response.json()['value']
    
    # Si no está en cache, consultar microservicio y guardar
    inventarios = consultar_microservicio(producto_id)
    
    # Guardar en cache
    requests.post('http://redis_service:5011/api/cache/', json={
        'key': f'inventarios:producto:{producto_id}',
        'value': inventarios,
        'ttl': 3600
    })
    
    return inventarios
```

## 🐳 Docker Compose

Agregar al `docker-compose.yml` raíz:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis_service:
    build: ./redis_service
    ports:
      - "5011:5011"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - PORT=5011
    depends_on:
      redis:
        condition: service_healthy

volumes:
  redis_data:
```

## 📊 Convenciones de Claves

### Cache de Inventarios
- `inventarios:producto:{producto_id}` - Lista de inventarios por producto
- `inventarios:sucursal:{sucursal_id}` - Inventarios por sucursal
- `inventarios:{inventario_id}` - Inventario específico

### Canales Pub/Sub
- `inventarios_updates` - Actualizaciones de inventarios
- `inventarios_creates` - Nuevos inventarios
- `inventarios_deletes` - Eliminaciones

## 🔍 Monitoreo

```bash
# Ver logs del servicio
docker-compose logs -f redis_service

# Ver estadísticas de Redis
curl http://localhost:5011/stats

# Verificar canales activos
curl http://localhost:5011/api/queue/channels

# Ver claves en cache
curl "http://localhost:5011/api/cache/keys?pattern=*"
```

## 🛠️ Desarrollo Local

```bash
cd redis_service

# Instalar dependencias
pip install -r requirements.txt

# Levantar Redis local
docker run -d -p 6379:6379 redis:7-alpine

# Ejecutar servicio
python run.py
```

## 📝 Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `PORT` | Puerto del servicio | `5011` |
| `REDIS_HOST` | Host de Redis | `redis` |
| `REDIS_PORT` | Puerto de Redis | `6379` |
| `REDIS_DB` | Base de datos Redis | `0` |
| `CACHE_DEFAULT_TTL` | TTL por defecto (segundos) | `3600` |
| `QUEUE_CHANNEL` | Canal Pub/Sub por defecto | `inventarios_updates` |

## 🧪 Testing

```bash
# Test de conexión
curl http://localhost:5011/health

# Test de cache
curl -X POST http://localhost:5011/api/cache/ \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "hello"}'

curl http://localhost:5011/api/cache/test

# Test de cola
curl -X POST http://localhost:5011/api/queue/publish \
  -H "Content-Type: application/json" \
  -d '{"channel": "test_channel", "message": {"hello": "world"}}'
```

## 📚 Recursos

- [Redis Documentation](https://redis.io/docs/)
- [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)
- [Flask Documentation](https://flask.palletsprojects.com/)
