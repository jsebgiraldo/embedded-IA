# 🐳 Docker Deployment Guide

Este documento explica cómo usar Docker Compose para ejecutar todo el stack del ESP32 Developer Agent con Dashboard.

## 📋 Stack de Servicios

El `docker-compose.yml` incluye:

### 1. **web-dashboard** (Puerto 8000)
- Dashboard web con monitoreo en tiempo real
- API REST para gestión de agentes, jobs y logs
- WebSocket para actualizaciones en vivo
- Base de datos SQLite persistente

### 2. **dev** (ESP-IDF)
- Contenedor principal con ESP-IDF
- Agentes de desarrollo (developer, test, build)
- Acceso a dispositivos seriales
- Conexión a LLM (Docker Desktop Models)

### 3. **mcp-server**
- Model Context Protocol Server
- Herramientas especializadas para ESP32
- Compilación, análisis y testing

## 🚀 Inicio Rápido

### Usando el script de gestión (Recomendado)

```bash
# Ver ayuda
./docker-manager.sh help

# Iniciar todos los servicios
./docker-manager.sh start

# Ver estado
./docker-manager.sh status

# Ver logs del dashboard
./docker-manager.sh logs web-dashboard

# Entrar en contenedor dev
./docker-manager.sh exec dev

# Detener servicios
./docker-manager.sh stop
```

### Usando docker-compose directamente

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f web-dashboard

# Detener servicios
docker-compose down

# Reconstruir servicios
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 Acceso a Servicios

Una vez iniciados los servicios:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Dashboard | http://localhost:8000 | Interfaz web principal |
| API Docs | http://localhost:8000/docs | Documentación Swagger de la API |
| WebSocket | ws://localhost:8000/ws | Endpoint WebSocket para eventos en tiempo real |
| LLM | http://localhost:11434 | Docker Desktop Models (qwen3-coder:latest) |

## 📁 Volúmenes Persistentes

```yaml
volumes:
  - ./workspace:/workspace              # Código ESP32
  - ./agent:/agent                      # Código de agentes
  - ./web-server:/app                   # Código del dashboard (hot reload)
  - dashboard-data:/app/data            # Base de datos SQLite
  - pip-cache:/root/.cache/pip          # Cache de pip
```

## 🔧 Comandos Útiles

### Ver estado de contenedores
```bash
docker-compose ps
```

### Ejecutar comandos en contenedores

```bash
# En contenedor dev
docker-compose exec dev bash
docker-compose exec dev idf.py build

# En contenedor web-dashboard
docker-compose exec web-dashboard bash
docker-compose exec web-dashboard python3 -c "from database.db import get_db; print('DB OK')"
```

### Ver logs en tiempo real
```bash
# Todos los servicios
docker-compose logs -f

# Solo web-dashboard
docker-compose logs -f web-dashboard

# Solo dev
docker-compose logs -f dev
```

### Reiniciar un servicio específico
```bash
docker-compose restart web-dashboard
```

### Reconstruir un servicio específico
```bash
docker-compose build web-dashboard
docker-compose up -d web-dashboard
```

## 🩺 Health Checks

El dashboard incluye health checks automáticos:

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/api/agents || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

Para ver el estado de salud:
```bash
docker-compose ps
```

## 🔄 Hot Reload

El dashboard soporta hot reload durante desarrollo:
- Los archivos en `./web-server` están montados como volumen
- Los cambios en Python se reflejan automáticamente (excepto `main.py`)
- Para cambios en `main.py`, reinicia el contenedor:
  ```bash
  docker-compose restart web-dashboard
  ```

## 🗄️ Base de Datos

La base de datos SQLite está persistida en el volumen `dashboard-data`:

```bash
# Backup manual
docker-compose exec web-dashboard cp /app/data/agent_dashboard.db /app/data/backup.db

# Usar script de gestión
./docker-manager.sh backup

# Ver estructura
docker-compose exec web-dashboard sqlite3 /app/data/agent_dashboard.db ".schema"

# Consultar datos
docker-compose exec web-dashboard sqlite3 /app/data/agent_dashboard.db "SELECT * FROM agents;"
```

## 🌐 Networking

Los servicios están conectados por una red bridge `esp32-network`:

- `web-dashboard` puede comunicarse con `dev` y `mcp-server`
- Todos pueden acceder a `host.docker.internal:11434` (Docker Desktop Models)
- El host puede acceder a `localhost:8000` (dashboard)

## 🧹 Limpieza

```bash
# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar contenedores y volúmenes (⚠️ elimina la base de datos)
docker-compose down -v

# Limpiar imágenes no usadas
docker system prune -f

# Limpieza completa con script
./docker-manager.sh clean
```

## 🐛 Troubleshooting

### El dashboard no inicia
```bash
# Ver logs
docker-compose logs web-dashboard

# Verificar que el puerto 8000 esté libre
lsof -i :8000

# Reconstruir imagen
docker-compose build --no-cache web-dashboard
docker-compose up -d web-dashboard
```

### No se puede conectar a Docker Desktop Models
```bash
# Verificar que Docker Desktop Models esté corriendo
curl http://localhost:11434/api/tags

# Verificar conectividad desde contenedor
docker-compose exec dev curl http://host.docker.internal:11434/api/tags
```

### Problemas con permisos de dispositivos seriales
```bash
# En Linux, agregar usuario al grupo dialout
sudo usermod -a -G dialout $USER

# En macOS, usar privileged: true (ya configurado)
```

### Base de datos corrupta
```bash
# Eliminar volumen y recrear
docker-compose down -v
docker-compose up -d web-dashboard
```

## 📊 Monitoreo de Recursos

```bash
# Ver uso de recursos
docker stats

# Ver uso de un contenedor específico
docker stats esp32-web-dashboard
```

## 🔐 Variables de Entorno

Puedes sobrescribir variables creando un archivo `.env`:

```bash
# .env
ESP_IDF_TARGET=esp32s3
OPENAI_API_KEY=your-key-here
LLM_MODEL=qwen3-coder:latest
```

## 📝 Desarrollo del Dashboard

Para desarrollo activo del dashboard:

1. Los cambios en archivos Python se auto-recargan
2. Los cambios en HTML/CSS/JS se reflejan inmediatamente (refresca el navegador)
3. Para cambios en `main.py` o `requirements.txt`:
   ```bash
   docker-compose restart web-dashboard
   ```

## 🚢 Despliegue en Producción

Para producción, considera:

1. **Usar variables de entorno** para secretos
2. **Configurar límites de recursos**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```
3. **Habilitar logging a archivo**
4. **Usar reverse proxy (nginx)** para HTTPS
5. **Configurar backups automáticos** de la base de datos

## 📚 Referencias

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [ESP-IDF Docker](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/tools/idf-docker-image.html)
- [FastAPI Docker](https://fastapi.tiangolo.com/deployment/docker/)
