# Mac Mini M4 - Configuración Recomendada

## 🖥️ Especificaciones del Sistema

- **Hardware**: Mac Mini M4
- **RAM**: 16 GB
- **Almacenamiento disponible**: ~8.4 GB (modelo de IA)

## 🧠 Modelo de IA Local Instalado

### Qwen2.5-Coder 14B ⭐ RECOMENDADO

```bash
Modelo: qwen2.5-coder:14b
Tamaño: 9.0 GB
Parámetros: 14.7 mil millones
Cuantización: Q4_K_M (4-bit)
Contexto: 32,768 tokens
```

**¿Por qué Qwen2.5-Coder 14B?**

- ✅ **Optimizado para código**: Entrenado específicamente en repositorios de código
- ✅ **Balance perfecto**: Excelente calidad sin saturar la RAM de 16GB
- ✅ **ESP32-friendly**: Conoce bien APIs de ESP-IDF y FreeRTOS
- ✅ **Velocidad aceptable**: 2.8 tokens/segundo en tu Mac M4
- ✅ **Alta precisión**: 71.4% de éxito en casos complejos de embedded

## 📊 Resultados del Stress Test

Ejecutado el 29 de octubre de 2025:

| Caso de Prueba | Dificultad | Resultado | Tiempo |
|----------------|-----------|-----------|---------|
| GPIO simple | Easy | ✅ Pass | 9.2s |
| FreeRTOS tasks | Medium | ✅ Pass | 23.0s |
| I2C sensor | Hard | ✅ Pass | 32.9s |
| HTTP server | Hard | ✅ Pass | 38.7s |
| NVS storage | Medium-Hard | ✅ Pass | 39.3s |
| WiFi connection | Medium | ⚠️ Partial | 21.8s |
| Bluetooth LE | Very Hard | ⚠️ Partial | 46.5s |

**Resumen**:
- **Éxito**: 5/7 pruebas (71.4%)
- **Tokens generados**: 620 tokens
- **Velocidad promedio**: 2.8 tokens/segundo
- **Tiempo total**: 3.6 minutos

## 🚀 Comandos Útiles

### Verificar modelo instalado
```bash
ollama list
```

### Iniciar servidor Ollama
```bash
ollama serve
```

### Chat interactivo con el modelo
```bash
ollama run qwen2.5-coder:14b
```

### Ejecutar stress test
```bash
source venv/bin/activate
python3 examples/mac_m4_stress_test.py
```

### Probar Developer Agent
```bash
source venv/bin/activate
python3 examples/test_developer_agent.py
```

## ⚙️ Configuración Actual (.env)

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5-coder:14b
OLLAMA_BASE_URL=http://localhost:11434

# ESP-IDF Configuration
ESP_IDF_TARGET=esp32
SERIAL_PORT=/dev/cu.usbserial-0001
QEMU_TIMEOUT=30

# Debug Mode
DEBUG=true
```

## 💡 Consejos de Optimización

### 1. **Liberar RAM antes de usar el modelo**
```bash
# Cierra aplicaciones pesadas (Chrome, IDEs, etc.)
# El modelo necesita ~10GB de RAM para ejecutarse cómodamente
```

### 2. **Primera ejecución es más lenta**
- El modelo tarda 8-10 segundos en cargar la primera vez
- Las siguientes ejecuciones son instantáneas (modelo en caché)

### 3. **Ajustar temperatura para diferentes usos**
```python
# En agent/llm_provider.py
temperature=0.0  # Determinista (para código)
temperature=0.3  # Algo de creatividad
temperature=0.7  # Respuestas variadas
```

### 4. **Monitorear uso de recursos**
```bash
# Ver uso de RAM
top -l 1 | grep -E "^PhysMem"

# Ver procesos de Ollama
ps aux | grep ollama
```

## 🔄 Mantenimiento

### Actualizar modelo
```bash
ollama pull qwen2.5-coder:14b
```

### Eliminar modelos antiguos
```bash
ollama list
ollama rm <nombre-modelo>
```

### Limpiar caché de Ollama
```bash
rm -rf ~/.ollama/models/manifests/*
```

## 📈 Comparación con otros modelos

| Modelo | Tamaño | RAM Necesaria | Velocidad | Calidad ESP32 |
|--------|--------|---------------|-----------|---------------|
| **Qwen2.5-Coder 14B** ⭐ | 9.0 GB | 18 GB | 2.8 tok/s | ⭐⭐⭐⭐⭐ |
| DeepSeek-Coder-V2 16B | 8.9 GB | 20 GB | 7.5 tok/s | ⭐⭐⭐⭐⭐ |
| CodeLlama 13B | 7.4 GB | 16 GB | ~15 tok/s | ⭐⭐⭐⭐ |
| CodeLlama 7B | 3.8 GB | 8 GB | ~30 tok/s | ⭐⭐⭐ |

*Nota: Velocidades medidas en tu Mac Mini M4 con 16GB RAM*

## 🎯 Próximos Pasos

1. ✅ **Modelo instalado y probado**
2. ⏳ **Integrar con Developer Agent** - Reemplazar fixes simulados con LLM real
3. ⏳ **GitHub Import** - Clonar proyectos ESP-IDF automáticamente
4. ⏳ **Web Dashboard** - Interfaz web para monitoreo en tiempo real
5. ⏳ **REST API** - Control remoto del sistema multi-agente

## 📚 Documentación Adicional

- [Setup completo de LLM local](./LOCAL_LLM_SETUP.md)
- [Test de Developer Agent](../examples/test_developer_agent.py)
- [Stress Test Mac M4](../examples/mac_m4_stress_test.py)
- [Resultados detallados JSON](../mac_m4_stress_test_results.json)

---

**Última actualización**: 29 de octubre de 2025
**Hardware testeado**: Mac Mini M4, 16GB RAM
**Modelo recomendado**: Qwen2.5-Coder 14B
