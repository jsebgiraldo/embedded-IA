# 🤖 Interactuando con el LLM (Qwen2.5-Coder)

Este documento explica todas las formas de interactuar con el LLM local que usa el sistema para generar y corregir código ESP32.

## 🎯 Formas de Uso

### 1. **Script Rápido (Recomendado)** ⚡

```bash
# Pregunta directa
./scripts/chat-llm.sh "How do I use I2C on ESP32?"

# Modo interactivo (chat continuo)
./scripts/chat-llm.sh
```

### 2. **Ollama CLI (Nativo)** 🔧

```bash
# Modo chat interactivo
docker exec -it esp32-ollama ollama run qwen2.5-coder:7b

# Pregunta directa
docker exec esp32-ollama ollama run qwen2.5-coder:7b "Explain ESP32 GPIO pins"

# Ver modelos instalados
docker exec esp32-ollama ollama list

# Ver información del modelo
docker exec esp32-ollama ollama show qwen2.5-coder:7b
```

Comandos dentro del chat interactivo:
- `/?` - Ayuda
- `/show` - Info del modelo
- `/clear` - Limpiar contexto
- `/bye` - Salir
- `"""` - Mensaje multi-línea

### 3. **API HTTP** 🌐

```bash
# Generar respuesta (sin streaming)
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write ESP32 code to read a DHT22 sensor",
  "stream": false
}' | jq -r '.response'

# Chat con contexto
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5-coder:7b",
  "messages": [
    {"role": "system", "content": "You are an ESP32 expert"},
    {"role": "user", "content": "How do I configure UART?"}
  ],
  "stream": false
}' | jq -r '.message.content'

# Streaming (ver respuesta en tiempo real)
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Explain FreeRTOS tasks",
  "stream": true
}'
```

### 4. **Desde Python** 🐍

```python
# Usando el script incluido
cd examples
python3 chat_with_llm.py "How do I use ESP-NOW?"

# Modo interactivo
python3 chat_with_llm.py
```

```python
# En tus propios scripts
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_provider import LLMConfig, get_llm, LLMProvider

# Configurar LLM
config = LLMConfig(
    provider=LLMProvider.OLLAMA,
    model="qwen2.5-coder:7b",
    temperature=0.1  # 0.0-1.0 (determinístico → creativo)
)

# Obtener LLM
llm = get_llm(config)

# Hacer pregunta
response = llm.invoke("How do I use ADC on ESP32?")
print(response)
```

### 5. **Code Fixer (Automático)** 🔧

El sistema usa el LLM automáticamente cuando detecta errores:

```python
from agent.code_fixer import create_code_fixer

# Crear fixer (lee config desde .env)
fixer = create_code_fixer()

# Arreglar código con error
result = fixer.fix_code(
    buggy_code=code_with_error,
    error_message="implicit declaration of function 'gpio_set_level'",
    filename="main.c"
)

if result.success:
    print(f"Fixed! Changes: {result.changes_made}")
    print(result.fixed_code)
```

## ⚙️ Configuración

El LLM lee su configuración de `.env`:

```bash
# Proveedor y modelo
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5-coder:7b

# URLs (desde host / desde containers)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_INTERNAL_URL=http://ollama:11434

# Parámetros de generación
LLM_TEMPERATURE=0.1        # 0.0 = determinístico, 1.0 = creativo
LLM_MAX_TOKENS=4096        # Longitud máxima de respuesta
```

## 📊 Ejemplos de Uso

### Generar código desde cero
```bash
./scripts/chat-llm.sh "Write complete ESP32 code for a web server that controls 2 LEDs via HTTP API"
```

### Explicar código existente
```bash
./scripts/chat-llm.sh "Explain this ESP32 code: $(cat workspace/main/main.c)"
```

### Debugging
```bash
./scripts/chat-llm.sh "Why do I get 'Guru Meditation Error: Core 0 panic'ed (LoadProhibited)' in ESP32?"
```

### Optimización
```bash
./scripts/chat-llm.sh "How can I reduce power consumption in this ESP32 deep sleep code?"
```

### Mejores prácticas
```bash
./scripts/chat-llm.sh "What are the security best practices for ESP32 WiFi connections?"
```

## 🔄 Cambiar de Modelo

```bash
# Listar modelos disponibles en Ollama
docker exec esp32-ollama ollama list

# Descargar un modelo diferente
docker exec esp32-ollama ollama pull deepseek-coder-v2:16b

# Actualizar .env
LLM_MODEL=deepseek-coder-v2:16b

# O usar temporalmente
LLM_MODEL=deepseek-coder-v2:16b ./scripts/chat-llm.sh "Your question"
```

### Modelos Recomendados

| Modelo | Tamaño | Uso | Velocidad | Calidad |
|--------|--------|-----|-----------|---------|
| `qwen2.5-coder:7b` | 4.7 GB | General ✅ | Rápida | Buena |
| `qwen2.5-coder:14b` | ~9 GB | Producción | Media | Excelente |
| `deepseek-coder-v2:16b` | ~10 GB | Mejor calidad | Lenta | Superior |
| `codellama:13b` | ~7 GB | Alternativa | Rápida | Buena |

## 🚀 Integración con el Sistema

El LLM se usa automáticamente en estos componentes:

1. **Developer Agent**: Arregla errores de compilación
2. **QA Agent**: Analiza resultados de tests y sugiere mejoras
3. **Orchestrator**: Coordina el workflow de build → fix → test
4. **Code Fixer**: API programática para fixes automáticos

Ver `agent/orchestrator.py` y `agent/code_fixer.py` para más detalles.

## 🔍 Troubleshooting

### LLM no responde
```bash
# Verificar que el contenedor esté corriendo
docker ps | grep esp32-ollama

# Ver logs
docker logs esp32-ollama --tail 50

# Reiniciar
docker-compose restart ollama
```

### Respuestas lentas
```bash
# Usar un modelo más pequeño
LLM_MODEL=qwen2.5-coder:7b

# Reducir tokens máximos
LLM_MAX_TOKENS=2048
```

### Modelo no encontrado
```bash
# Descargar el modelo
docker exec esp32-ollama ollama pull qwen2.5-coder:7b
```

## 📚 Recursos

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen2.5-Coder Paper](https://qwenlm.github.io/blog/qwen2.5/)
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/)

## 💡 Tips

1. **Sé específico**: "Show me how to initialize I2C on ESP32-S3 with pins 21 and 22" vs "How do I use I2C?"
2. **Incluye contexto**: "I'm getting error X, here's my code: [code]"
3. **Ajusta temperatura**: 
   - 0.0-0.3 para código (determinístico)
   - 0.5-0.7 para explicaciones (balance)
   - 0.8-1.0 para brainstorming (creativo)
4. **Usa system prompts**: Configura el rol del LLM para mejores respuestas
