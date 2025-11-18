# 🌐 ESP32 Dashboard - LLM Integration Guide

El dashboard ahora incluye integración completa con LLM para desarrollo asistido por IA.

## 🎯 Funcionalidades Nuevas

### 1. **💬 Chat con LLM** 
Interfaz de chat interactivo para hacer preguntas sobre ESP32.

**Características:**
- Respuestas en tiempo real
- Historial de conversación
- Control de "temperatura" (creatividad)
- Preguntas rápidas predefinidas
- Formateo de código en las respuestas

**Ejemplos de uso:**
- "How do I initialize WiFi on ESP32?"
- "Show me how to use GPIO interrupts"
- "Explain FreeRTOS tasks"
- "What are the best practices for power management?"

### 2. **⚡ Generador de Código**
Genera código ESP32 completo desde descripciones en lenguaje natural.

**Características:**
- Genera código production-ready
- Incluye headers necesarios
- Comentarios explicativos
- Explicación detallada del código
- Copia con un click

**Ejemplo:**
```
Input: "Create a web server that controls 2 LEDs via HTTP API"
Output: Código completo con:
- Configuración WiFi
- HTTP server setup
- Endpoints para cada LED
- Manejo de errores
```

### 3. **🔧 Reparador de Código**
Fix automático de errores de compilación usando IA.

**Características:**
- Diagnóstico del problema
- Fix automático del código
- Lista de cambios realizados
- Nivel de confianza (high/medium/low)
- Código reparado listo para copiar

**Ejemplo:**
```
Error: implicit declaration of function 'gpio_set_direction'
Fix: Agrega #include "driver/gpio.h"
Confidence: high
```

## 🚀 Cómo Usar

### Acceso al Dashboard

```bash
# El dashboard está en:
http://localhost:8000

# Tabs disponibles:
📊 Dashboard - Monitoreo en tiempo real
💬 LLM Chat - Chat con el asistente
⚡ Code Generator - Genera código
🔧 Code Fixer - Repara errores
```

### Uso del Chat

1. **Click en "💬 LLM Chat"**
2. **Escribe tu pregunta** en el campo de texto
3. **Presiona Enter o click en "Send"**
4. **El LLM responde** en tiempo real

**Atajos:**
- `Enter` - Enviar mensaje
- `Shift + Enter` - Nueva línea
- Botones de acciones rápidas en el sidebar

### Uso del Generador

1. **Click en "⚡ Code Generator"**
2. **Describe** lo que quieres construir
3. **Selecciona** lenguaje y framework
4. **Click en "Generate Code"**
5. **Copia** el código generado

**Tips:**
- Sé específico en la descripción
- Menciona pines GPIO si es relevante
- Indica protocolos (I2C, SPI, UART, etc.)
- Especifica target ESP32 (S2, S3, C3, etc.)

### Uso del Code Fixer

1. **Click en "🔧 Code Fixer"**
2. **Pega** tu código con errores
3. **Pega** el mensaje de error
4. **Especifica** filename y component
5. **Click en "Fix Code"**
6. **Revisa** el diagnóstico y cambios
7. **Copia** el código reparado

## 🔧 API Endpoints

Todos los endpoints están disponibles en `/api/llm`:

### GET `/api/llm/status`
Verifica estado del LLM

```bash
curl http://localhost:8000/api/llm/status
```

**Response:**
```json
{
  "available": true,
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "base_url": "http://ollama:11434"
}
```

### POST `/api/llm/chat`
Chat con el LLM

```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I use I2C on ESP32?",
    "temperature": 0.7
  }'
```

**Request:**
```json
{
  "message": "string",
  "temperature": 0.7,
  "system_prompt": "optional string"
}
```

**Response:**
```json
{
  "response": "string",
  "model": "qwen2.5-coder:7b",
  "timestamp": "2025-11-17T..."
}
```

### POST `/api/llm/generate`
Genera código

```bash
curl -X POST http://localhost:8000/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Blink LED on GPIO 2",
    "language": "c",
    "framework": "esp-idf",
    "temperature": 0.1
  }'
```

**Request:**
```json
{
  "description": "string",
  "language": "c",
  "framework": "esp-idf",
  "temperature": 0.1
}
```

**Response:**
```json
{
  "code": "string",
  "explanation": "string",
  "model": "qwen2.5-coder:7b",
  "timestamp": "2025-11-17T..."
}
```

### POST `/api/llm/fix`
Repara código

```bash
curl -X POST http://localhost:8000/api/llm/fix \
  -H "Content-Type: application/json" \
  -d '{
    "buggy_code": "your code...",
    "error_message": "error message...",
    "filename": "main.c",
    "component": "main"
  }'
```

**Request:**
```json
{
  "buggy_code": "string",
  "error_message": "string",
  "filename": "main.c",
  "component": "main"
}
```

**Response:**
```json
{
  "success": true,
  "fixed_code": "string",
  "changes_made": ["list of changes"],
  "confidence": "high",
  "diagnosis": "string"
}
```

### POST `/api/llm/analyze`
Analiza código

```bash
curl -X POST http://localhost:8000/api/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "your code...",
    "analysis_type": "general"
  }'
```

**Analysis types:**
- `general` - Análisis general
- `error` - Análisis de errores (requiere `error_message`)
- `optimization` - Sugerencias de optimización

## ⚙️ Configuración

### Variables de Entorno

El dashboard lee estas variables de `.env`:

```bash
# LLM Provider
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5-coder:7b

# Ollama URLs
OLLAMA_BASE_URL=http://localhost:11434        # Desde host
OLLAMA_INTERNAL_URL=http://ollama:11434       # Desde containers

# Generation Parameters
LLM_TEMPERATURE=0.1        # 0.0-1.0 (deterministic → creative)
LLM_MAX_TOKENS=4096        # Max response length
```

### Ajustar Temperatura

**En la UI:**
- Chat: Slider en sidebar (0.0 - 1.0)
- Generator: Dropdown con presets
- Fixer: Usa valor fijo óptimo (0.1)

**Guía de temperatura:**
- `0.0 - 0.2`: Muy determinístico (código)
- `0.3 - 0.5`: Balanceado (explicaciones)
- `0.6 - 0.8`: Creativo (brainstorming)
- `0.9 - 1.0`: Muy creativo (puede ser impredecible)

### Cambiar Modelo

```bash
# En .env
LLM_MODEL=deepseek-coder-v2:16b

# O descargar nuevo modelo
docker exec esp32-ollama ollama pull deepseek-coder-v2:16b

# Reiniciar dashboard
docker-compose restart web-dashboard
```

## 🎨 Personalización

### Agregar Preguntas Rápidas

Edita `/web-server/static/index.html`:

```html
<button class="quick-action-btn" onclick="sendQuickQuestion('Your question')">
    🔥 Your Label
</button>
```

### Modificar System Prompts

Edita `/web-server/api/routes/llm.py`:

```python
system_prompt = (
    "You are an expert ESP32 developer. "
    "Your custom instructions here..."
)
```

### Agregar Nuevas Funcionalidades

1. **Backend**: Agrega endpoint en `api/routes/llm.py`
2. **Frontend**: Agrega función en `static/js/llm.js`
3. **UI**: Agrega elementos en `static/index.html`
4. **Estilos**: Agrega CSS en `static/css/llm.css`

## 📊 Uso con Workflows

El LLM se integra automáticamente con el Developer Agent:

```python
from agent.orchestrator import AgentOrchestrator

# El orquestador usa el LLM automáticamente
orchestrator = AgentOrchestrator(
    langchain_tools=tools,
    llm_provider="ollama",
    llm_model="qwen2.5-coder:7b"
)

# Cuando QA detecta un error, Developer Agent lo arregla
result = await orchestrator.run_workflow()
# El LLM genera el fix automáticamente
```

## 🔍 Debugging

### LLM No Responde

```bash
# Verificar estado
curl http://localhost:8000/api/llm/status

# Verificar logs del dashboard
docker logs esp32-web-dashboard --tail 50

# Verificar logs de Ollama
docker logs esp32-ollama --tail 50

# Reiniciar servicios
docker-compose restart ollama web-dashboard
```

### Respuestas Lentas

- Usa modelo más pequeño (7b en vez de 14b)
- Reduce `LLM_MAX_TOKENS`
- Baja temperatura para respuestas más directas

### Errores de Conexión

```bash
# Desde el dashboard, debe llegar a ollama
docker exec esp32-web-dashboard curl http://ollama:11434/api/tags

# Si falla, verificar red
docker network inspect embedded-ia_esp32-network
```

## 📚 Ejemplos

### Ejemplo 1: Generar Código de Sensor

**Input:**
```
Read temperature from DHT22 sensor on GPIO 4.
Print to serial every 2 seconds.
Handle sensor errors gracefully.
```

**Output:**
```c
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "dht.h"

#define DHT_GPIO GPIO_NUM_4

void app_main(void) {
    gpio_set_pull_mode(DHT_GPIO, GPIO_PULLUP_ONLY);
    
    while(1) {
        float temperature = 0, humidity = 0;
        
        if (dht_read_float_data(DHT_TYPE_DHT22, DHT_GPIO, 
                                 &humidity, &temperature) == ESP_OK) {
            printf("Temperature: %.1f°C, Humidity: %.1f%%\n", 
                   temperature, humidity);
        } else {
            printf("Error reading DHT22 sensor\n");
        }
        
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
```

### Ejemplo 2: Fix de Error de WiFi

**Buggy Code:**
```c
#include "esp_wifi.h"

void app_main() {
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
}
```

**Error:**
```
undefined reference to `nvs_flash_init'
```

**Fixed Code:**
```c
#include "nvs_flash.h"
#include "esp_wifi.h"

void app_main() {
    // Initialize NVS (required for WiFi)
    ESP_ERROR_CHECK(nvs_flash_init());
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
}
```

**Diagnosis:**
WiFi requires NVS (Non-Volatile Storage) to be initialized first for storing configuration.

## 🎯 Best Practices

1. **Sé específico** en tus preguntas y descripciones
2. **Incluye contexto** relevante (target ESP32, pines, protocolos)
3. **Verifica el código** generado antes de usarlo en producción
4. **Usa temperatura baja** (0.1-0.3) para código
5. **Usa temperatura alta** (0.6-0.8) para brainstorming
6. **Revisa fixes** del LLM antes de aplicarlos
7. **Combina** chat + generator para mejor resultado

## 🆘 Soporte

- **Documentación completa**: `docs/LLM_USAGE.md`
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Chat en tiempo real**: Tab "💬 LLM Chat" en el dashboard

## 🎉 Próximas Funcionalidades

- [ ] Historial de conversaciones persistente
- [ ] Templates de código predefinidos
- [ ] Análisis de proyectos completos
- [ ] Sugerencias proactivas en logs
- [ ] Integración con GitHub Copilot
- [ ] Exportar código generado directo a archivos
- [ ] Comparación de código antes/después
- [ ] Métricas de uso del LLM
