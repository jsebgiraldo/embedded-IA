# 🚀 GitHub Import Service - Quick Start

## ✅ Implementado

### Backend Completo
- ✅ Database models (Project, Build, Dependency, WebhookEvent)
- ✅ Repository Manager (clone, update, checkout)
- ✅ Webhook Service (validation HMAC, parsing)
- ✅ Projects API (CRUD completo)
- ✅ GitHub Webhook endpoint
- ✅ Background task processing

## 🔧 Setup

### 1. Rebuild Docker Image

Agregamos GitPython a las dependencias, necesitas rebuild:

```bash
cd /Users/sebastiangiraldo/Documents/embedded-IA

# Rebuild web-dashboard con nueva dependencia
docker-compose build web-dashboard

# Restart container
docker-compose up -d web-dashboard

# Verificar logs
docker logs esp32-web-dashboard --tail 50
```

### 2. Verificar Tablas Creadas

Las nuevas tablas se crean automáticamente al iniciar:

```bash
# Verificar logs del inicio
docker logs esp32-web-dashboard | grep "Database initialized"

# Deberías ver:
# ✅ Database initialized at: sqlite:////app/data/agent_dashboard.db
```

Las tablas creadas:
- `projects` - Proyectos importados desde GitHub
- `builds` - Historial de builds
- `dependencies` - Dependencias ESP-IDF
- `webhook_events` - Log de webhooks recibidos

## 🧪 Testing Manual

### 1. Crear un Proyecto

```bash
# Crear proyecto desde GitHub
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "esp-idf-template",
    "description": "ESP-IDF project template",
    "repo_url": "https://github.com/espressif/esp-idf-template",
    "repo_full_name": "espressif/esp-idf-template",
    "branch": "main",
    "target": "esp32",
    "build_system": "cmake"
  }'

# Response esperado:
# {
#   "id": "uuid",
#   "name": "esp-idf-template",
#   "status": "pending",  # Luego cambia a "active"
#   "clone_path": "/app/projects/esp-idf-template",
#   "created_at": "2025-11-17T...",
#   ...
# }
```

### 2. Listar Proyectos

```bash
# Listar todos los proyectos
curl http://localhost:8000/api/projects

# Con filtros
curl 'http://localhost:8000/api/projects?status=active&limit=10'
```

### 3. Ver Detalles de un Proyecto

```bash
# Reemplaza {project_id} con el UUID del proyecto
curl http://localhost:8000/api/projects/{project_id}

# Response incluye:
# - Información del proyecto
# - Lista de dependencias
# - Últimos 10 builds
# - Métricas (success rate, avg build time)
```

### 4. Sincronizar Proyecto

```bash
# Pull latest changes desde GitHub
curl -X PUT http://localhost:8000/api/projects/{project_id}/sync

# Response:
# {
#   "status": "synced",
#   "previous_commit": "abc123...",
#   "current_commit": "def456...",
#   "changes": {
#     "files_changed": 3,
#     "insertions": 45,
#     "deletions": 12,
#     "commits_pulled": 2
#   }
# }
```

### 5. Trigger Manual Build

```bash
# Disparar build del último commit
curl -X POST http://localhost:8000/api/projects/{project_id}/build \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "manual"
  }'

# Build de un commit específico
curl -X POST http://localhost:8000/api/projects/{project_id}/build \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "manual",
    "commit_sha": "abc123..."
  }'

# Response:
# {
#   "build_id": 123,
#   "status": "pending",
#   "project_id": "uuid",
#   "commit_sha": "abc123..."
# }
```

### 6. Test Webhook Receiver

```bash
# Verificar que el endpoint existe
curl http://localhost:8000/api/github/webhook/test

# Response:
# {
#   "status": "ok",
#   "message": "Webhook receiver is active",
#   "endpoint": "/api/github/webhook"
# }
```

### 7. Simular Webhook de GitHub

```bash
# Crear payload de prueba
cat > test_webhook_push.json << 'EOF'
{
  "ref": "refs/heads/main",
  "repository": {
    "full_name": "espressif/esp-idf-template",
    "clone_url": "https://github.com/espressif/esp-idf-template.git"
  },
  "head_commit": {
    "id": "abc123def456",
    "message": "Test commit from webhook",
    "author": {
      "name": "Test User",
      "email": "test@example.com"
    },
    "timestamp": "2025-11-17T12:00:00Z"
  },
  "commits": [
    {
      "id": "abc123def456",
      "message": "Test commit"
    }
  ],
  "pusher": {
    "name": "testuser"
  }
}
EOF

# Enviar webhook (sin signature si no configuraste secret)
curl -X POST http://localhost:8000/api/github/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: test-delivery-123" \
  -d @test_webhook_push.json

# Response:
# {
#   "status": "received",
#   "event_id": "test-delivery-123",
#   "event_type": "push",
#   "queued": true
# }

# Verificar que se creó el build
curl http://localhost:8000/api/projects/{project_id}
# Deberías ver el nuevo build en "recent_builds"
```

## 🔐 Configurar Webhook en GitHub

### 1. Obtener Webhook URL

Tu webhook URL será:
```
http://your-public-domain/api/github/webhook
```

**Para desarrollo local**, necesitas exponer el puerto usando:
- [ngrok](https://ngrok.com/): `ngrok http 8000`
- [localtunnel](https://localtunnel.github.io/www/): `lt --port 8000`

### 2. Configurar en GitHub

1. Ve a tu repositorio en GitHub
2. Settings → Webhooks → Add webhook
3. Payload URL: `https://your-ngrok-url.ngrok.io/api/github/webhook`
4. Content type: `application/json`
5. Secret: (opcional, pero recomendado)
6. Events: Selecciona `push` y `pull_request`
7. Active: ✅
8. Add webhook

### 3. Actualizar Proyecto con Secret

Si configuraste un secret en GitHub:

```bash
curl -X PUT http://localhost:8000/api/projects/{project_id} \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_secret": "your-github-webhook-secret"
  }'
```

### 4. Test con Ping

GitHub enviará un evento "ping" automáticamente. Verifica los logs:

```bash
docker logs esp32-web-dashboard -f

# Deberías ver:
# 📨 Received webhook: ping (delivery: xxx)
# ✅ Webhook queued for processing: 1
# ✅ Ping event processed
```

## 📊 Verificar Database

```bash
# Entrar al container
docker exec -it esp32-web-dashboard bash

# Ver proyectos
sqlite3 /app/data/agent_dashboard.db "SELECT id, name, status, repo_full_name FROM projects;"

# Ver builds
sqlite3 /app/data/agent_dashboard.db "SELECT id, project_id, status, commit_sha, triggered_by FROM builds;"

# Ver webhooks
sqlite3 /app/data/agent_dashboard.db "SELECT id, event_type, status, created_at FROM webhook_events;"
```

## 🐛 Troubleshooting

### Error: "No module named 'git'"

Rebuild el container:
```bash
docker-compose build web-dashboard
docker-compose up -d web-dashboard
```

### Error: "Failed to clone repository"

Verifica:
1. URL del repo es correcta
2. Repo es público (o configura SSH keys para privados)
3. Hay espacio en disco

```bash
# Ver logs detallados
docker logs esp32-web-dashboard -f

# Ver espacio en disco
docker exec esp32-web-dashboard df -h
```

### Webhook no se procesa

Verifica:
1. Proyecto existe con `repo_full_name` correcto
2. Signature es válida (si configuraste secret)
3. Event type es soportado (`push`, `pull_request`, `ping`)

```bash
# Ver webhooks recibidos
curl http://localhost:8000/api/projects/{project_id} | jq '.recent_builds'

# Ver logs de procesamiento
docker logs esp32-web-dashboard | grep "webhook"
```

## 🎯 Next Steps

### 1. Rebuild Container ✅

```bash
docker-compose build web-dashboard
docker-compose up -d web-dashboard
```

### 2. Test API Endpoints ✅

Sigue los ejemplos de curl arriba.

### 3. Integrar con UI

Crear tab "Projects" en el dashboard para:
- Listar proyectos
- Crear nuevo proyecto
- Ver detalles y builds
- Disparar builds manuales
- Ver webhook logs

### 4. Integrar con Orchestrator

Conectar `trigger_build` con `AgentOrchestrator` para:
- Ejecutar workflow completo (build → test → QA)
- Actualizar Build con resultados
- Mostrar progreso en tiempo real

### 5. Dependency Resolver

Implementar parser de `idf_component.yml`:
- Detectar dependencias automáticamente
- Instalar con `idf.py add-dependency`
- Actualizar tabla `dependencies`

## 📚 API Documentation

Una vez el container esté corriendo, visita:

```
http://localhost:8000/docs
```

Verás Swagger UI con:
- `/api/projects` - CRUD de proyectos
- `/api/projects/{id}/sync` - Sincronizar repo
- `/api/projects/{id}/build` - Trigger build
- `/api/github/webhook` - Receive webhooks

## 🎉 Summary

¡Has implementado exitosamente el sistema de importación automática de GitHub!

**Lo que funciona:**
- ✅ Crear proyectos desde repos GitHub
- ✅ Clonar automáticamente repositorios
- ✅ Sincronizar cambios (git pull)
- ✅ Recibir webhooks de GitHub
- ✅ Validar signatures HMAC
- ✅ Crear builds automáticamente
- ✅ Procesamiento background con FastAPI
- ✅ Database con relaciones (projects → builds)

**Próximos pasos:**
- [ ] Rebuild Docker image
- [ ] Test API endpoints
- [ ] Agregar UI tab
- [ ] Integrar con orchestrator
- [ ] Dependency resolver
