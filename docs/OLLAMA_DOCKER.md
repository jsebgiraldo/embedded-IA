# 🐳 Ollama en Docker - Guía de Uso

## 📋 Índice
- [Ventajas de Docker](#ventajas)
- [Inicio Rápido](#inicio-rápido)
- [Comandos Disponibles](#comandos)
- [Integración con Agent](#integración)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Ventajas de Usar Ollama en Docker

### ✅ Beneficios

1. **Aislamiento de Recursos**
   - Control preciso de RAM (límite 12GB en compose)
   - No interfiere con otros procesos del sistema
   - Fácil de detener/reiniciar

2. **Portabilidad**
   - Mismo setup en Mac, Linux, Windows
   - Configuración reproducible
   - Fácil de compartir con el equipo

3. **Gestión Simplificada**
   - Un solo comando para iniciar/detener
   - Health checks automáticos
   - Logs centralizados

4. **Networking**
   - Los contenedores dev/mcp-server se comunican directamente
   - URL consistente: `http://ollama:11434`
   - No hay conflictos de puertos

5. **Persistencia**
   - Modelos se guardan en volumen Docker
   - No se pierden al reiniciar
   - Fácil backup/restore

---

## 🚀 Inicio Rápido

### 1️⃣ Iniciar Ollama

```bash
# Opción A: Con el helper script (recomendado)
./scripts/ollama-docker.sh start

# Opción B: Con docker-compose
docker-compose up -d ollama
```

### 2️⃣ Descargar Modelo

```bash
# Con el helper script
./scripts/ollama-docker.sh pull qwen2.5-coder:14b

# Manual
docker exec esp32-ollama ollama pull qwen2.5-coder:14b
```

### 3️⃣ Verificar Estado

```bash
./scripts/ollama-docker.sh status
```

Salida esperada:
```
╔══════════════════════════════════════════════════════════════╗
║          Ollama Docker Manager - ESP32 DevAgent             ║
╚══════════════════════════════════════════════════════════════╝

✅ Estado: CORRIENDO

📊 Recursos:
  CPU: 5.42%
  RAM: 8.5GB / 12GB

🤖 Modelos disponibles:
  qwen2.5-coder:14b     8.5GB    3 hours ago

🌐 Endpoint:
  http://localhost:11434
```

### 4️⃣ Test Rápido

```bash
./scripts/ollama-docker.sh test
```

---

## 📦 Comandos Disponibles

### Gestión Básica

```bash
# Iniciar
./scripts/ollama-docker.sh start

# Detener (libera RAM)
./scripts/ollama-docker.sh stop

# Reiniciar
./scripts/ollama-docker.sh restart

# Ver estado
./scripts/ollama-docker.sh status
```

### Modelos

```bash
# Descargar modelo
./scripts/ollama-docker.sh pull qwen2.5-coder:14b

# Chat interactivo
./scripts/ollama-docker.sh run qwen2.5-coder:14b

# Listar modelos
docker exec esp32-ollama ollama list

# Eliminar modelo (libera espacio)
docker exec esp32-ollama ollama rm qwen2.5-coder:14b
```

### Debugging

```bash
# Ver logs
./scripts/ollama-docker.sh logs

# Test de conectividad
./scripts/ollama-docker.sh test

# Entrar al contenedor
docker exec -it esp32-ollama bash

# Ver uso de recursos en tiempo real
docker stats esp32-ollama
```

---

## 🔌 Integración con Developer Agent

### Configuración

El `docker-compose.yml` ya está configurado para que los contenedores `dev` y `mcp-server` usen Ollama:

```yaml
environment:
  - LLM_PROVIDER=ollama
  - LLM_MODEL=qwen2.5-coder:14b
  - OLLAMA_BASE_URL=http://ollama:11434  # ← URL interna de Docker
```

### Uso desde el Agent

```python
# agent/llm_provider.py detecta automáticamente la URL correcta

# Ejemplo de uso
from agent.code_fixer import create_code_fixer

fixer = create_code_fixer(
    provider="ollama",
    model="qwen2.5-coder:14b"
)

result = fixer.fix_code(buggy_code, error_message)
print(result.fixed_code)
```

### Ejecutar Tests

```bash
# Iniciar todo el stack
docker-compose up -d

# Ejecutar tests desde el contenedor dev
docker exec -it esp32-idf-dev bash
cd /agent
python3 examples/test_developer_agent.py

# O desde tu Mac (si tienes las deps)
source venv/bin/activate
python3 examples/test_developer_agent.py --provider ollama
```

---

## 🔄 Workflows Recomendados

### Desarrollo Interactivo

```bash
# 1. Iniciar Ollama
./scripts/ollama-docker.sh start

# 2. Trabajar con Copilot (yo) para análisis rápido
# (No consume recursos de Ollama)

# 3. Cuando necesites batch processing
docker-compose exec dev python3 /agent/examples/test_developer_agent.py

# 4. Detener Ollama cuando termines
./scripts/ollama-docker.sh stop
```

### CI/CD Automatizado

```bash
# Script de CI/CD
./scripts/ollama-docker.sh start
docker-compose exec dev python3 /agent/examples/test_developer_agent.py --save
./scripts/ollama-docker.sh stop

# Analizar resultados
cat developer_agent_test_results.json
```

### Desarrollo Local vs Docker

#### Opción A: Todo en Docker (recomendado para CI/CD)
```bash
docker-compose up -d
docker exec -it esp32-idf-dev bash
# Todo está aislado, reproducible
```

#### Opción B: Híbrido (recomendado para desarrollo)
```bash
# Solo Ollama en Docker
./scripts/ollama-docker.sh start

# Agent en tu Mac
source venv/bin/activate
export OLLAMA_BASE_URL=http://localhost:11434
python3 examples/test_developer_agent.py
```

---

## 🧪 Comparación: Docker vs Local

| Aspecto | Ollama Local | Ollama Docker |
|---------|-------------|---------------|
| **Setup** | `brew install ollama` | `docker-compose up` |
| **RAM Control** | Manual | Automático (12GB limit) |
| **Portabilidad** | Solo Mac | Mac/Linux/Windows |
| **Inicio** | `ollama serve` | `./scripts/ollama-docker.sh start` |
| **URL** | `localhost:11434` | `localhost:11434` (externo)<br>`ollama:11434` (interno) |
| **Logs** | Terminal | `docker logs` |
| **Aislamiento** | No | Sí |
| **CI/CD** | Complejo | Simple |

---

## 🐛 Troubleshooting

### Problema: "Connection refused"

```bash
# Verificar que Ollama esté corriendo
docker ps | grep ollama

# Ver logs
docker logs esp32-ollama

# Reiniciar
./scripts/ollama-docker.sh restart
```

### Problema: "Out of memory"

```bash
# Ver uso actual
docker stats esp32-ollama

# Ajustar límite en docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 10G  # Reducir si es necesario
```

### Problema: "Model not found"

```bash
# Listar modelos
docker exec esp32-ollama ollama list

# Descargar el modelo
./scripts/ollama-docker.sh pull qwen2.5-coder:14b
```

### Problema: "Timeout waiting for Ollama"

```bash
# El modelo es grande y tarda en cargar
# Esperar 1-2 minutos la primera vez

# Ver progreso
docker logs -f esp32-ollama

# Verificar salud
docker inspect esp32-ollama | grep -A 10 Health
```

### Problema: URL incorrecta

```bash
# Desde tu Mac:
OLLAMA_BASE_URL=http://localhost:11434

# Desde contenedor Docker:
OLLAMA_BASE_URL=http://ollama:11434

# El agent detecta automáticamente, pero verifica:
echo $OLLAMA_BASE_URL
```

---

## 📊 Monitoreo de Recursos

### Ver uso en tiempo real

```bash
# Stats del contenedor
docker stats esp32-ollama --no-stream

# Stats de todos los servicios
docker stats --no-stream
```

### Benchmark

```bash
# Test de velocidad
time ./scripts/ollama-docker.sh test

# Comparar con local
time ollama run qwen2.5-coder:14b "Write hello world"
```

---

## 🔧 Configuración Avanzada

### Cambiar Modelo por Defecto

Edita `.env`:
```bash
LLM_MODEL=deepseek-coder-v2:16b
```

### Usar GPU (NVIDIA)

Edita `docker-compose.yml`:
```yaml
ollama:
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
```

### Persistent Logs

```yaml
ollama:
  volumes:
    - ollama-data:/root/.ollama
    - ./logs/ollama:/var/log/ollama  # ← Agregar
```

### Health Check Personalizado

```yaml
ollama:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
    interval: 10s  # Más frecuente
    timeout: 5s
    retries: 5
```

---

## 📚 Referencias

- [Ollama Docker Hub](https://hub.docker.com/r/ollama/ollama)
- [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Mac M4 Optimization Guide](./MAC_M4_SETUP.md)

---

## 🎯 Próximos Pasos

1. ✅ Ollama en Docker configurado
2. ⏳ Integrar `code_fixer` en `orchestrator.py`
3. ⏳ Auto-start/stop de Ollama
4. ⏳ Dashboard web con métricas
5. ⏳ CI/CD pipeline completo

---

**¿Preguntas?** Pregúntame en el chat! 🤖
