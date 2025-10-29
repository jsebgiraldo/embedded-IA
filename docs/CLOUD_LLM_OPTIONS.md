# Opciones de IA en la Nube - Comparación y Facturación

## 🌐 Proveedores Soportados

El sistema soporta **4 proveedores** de IA (3 en la nube + 1 local):

1. **Ollama** (Local) ⭐ *Gratis, privado, ya configurado*
2. **OpenAI** (Cloud) - GPT-4, GPT-4o-mini
3. **Anthropic** (Cloud) - Claude 3.5 Sonnet/Haiku
4. **Azure OpenAI** (Cloud) - GPT-4 con SLA empresarial

---

## 💰 Comparación de Costos (Octubre 2025)

### 1. OpenAI (https://openai.com/pricing)

#### GPT-4o (Modelo más potente)
- **Input**: $2.50 por 1M tokens (~750,000 palabras)
- **Output**: $10.00 por 1M tokens
- **Velocidad**: ~80 tokens/segundo
- **Contexto**: 128,000 tokens

**Costo estimado por uso ESP32:**
- Fix pequeño (GPIO): ~500 tokens = **$0.005 USD** (5 décimas de centavo)
- Fix complejo (BLE): ~2000 tokens = **$0.02 USD** (2 centavos)
- 1000 fixes al mes: **$10-20 USD/mes**

#### GPT-4o-mini ⭐ *Recomendado para desarrollo*
- **Input**: $0.150 por 1M tokens
- **Output**: $0.600 por 1M tokens
- **Velocidad**: ~100 tokens/segundo
- **Contexto**: 128,000 tokens

**Costo estimado por uso ESP32:**
- Fix pequeño (GPIO): ~500 tokens = **$0.0003 USD** (0.03 centavos)
- Fix complejo (BLE): ~2000 tokens = **$0.0012 USD** (0.12 centavos)
- **1000 fixes al mes: $0.60-1.20 USD/mes** 💚 *Muy económico*

#### GPT-3.5 Turbo (Más barato, menos calidad)
- **Input**: $0.50 por 1M tokens
- **Output**: $1.50 por 1M tokens
- **Velocidad**: ~120 tokens/segundo
- **Contexto**: 16,385 tokens

**Costo estimado:** Similar a GPT-4o-mini pero con menor calidad en código.

---

### 2. Anthropic Claude (https://anthropic.com/pricing)

#### Claude 3.5 Sonnet (Mejor en razonamiento)
- **Input**: $3.00 por 1M tokens
- **Output**: $15.00 por 1M tokens
- **Velocidad**: ~70 tokens/segundo
- **Contexto**: 200,000 tokens

**Costo estimado por uso ESP32:**
- Fix pequeño: ~$0.008 USD
- Fix complejo: ~$0.03 USD
- 1000 fixes al mes: **$15-30 USD/mes**

**Ventajas:**
- ✅ Excelente en debugging complejo
- ✅ Mejor comprensión de contexto largo
- ✅ Menos alucinaciones

#### Claude 3.5 Haiku (Rápido y económico)
- **Input**: $0.80 por 1M tokens
- **Output**: $4.00 por 1M tokens
- **Velocidad**: ~100 tokens/segundo
- **Contexto**: 200,000 tokens

**Costo estimado:** Similar a GPT-4o-mini con mejor calidad.

---

### 3. Azure OpenAI (https://azure.microsoft.com/pricing)

#### Modelo: GPT-4 (Igual que OpenAI pero con SLA)
- **Input**: $2.50-3.00 por 1M tokens
- **Output**: $10.00-12.00 por 1M tokens
- **SLA**: 99.9% uptime garantizado
- **Regiones**: Múltiples (incluye Latam)

**Ventajas:**
- ✅ SLA empresarial
- ✅ Integración con Azure DevOps
- ✅ Residencia de datos (cumplimiento GDPR)
- ✅ Facturación consolidada con Azure

**Desventajas:**
- ❌ Más caro (~20% premium)
- ❌ Requiere cuenta Azure
- ❌ Setup más complejo

---

### 4. Ollama (Local) ⭐ *CONFIGURADO*

#### Qwen2.5-Coder 14B (Ya instalado)
- **Costo**: **$0.00 USD** (gratis)
- **Hardware**: Mac Mini M4 (ya tienes)
- **Velocidad**: 2.8 tokens/segundo
- **RAM**: 10 GB requerida
- **Storage**: 9 GB

**Ventajas:**
- ✅ **Gratis** - sin costos recurrentes
- ✅ **Privado** - código nunca sale de tu máquina
- ✅ **Offline** - funciona sin internet
- ✅ **Sin límites** - requests ilimitados
- ✅ **Ya configurado** - listo para usar

**Desventajas:**
- ⚠️ Más lento (2.8 vs 80 tok/s)
- ⚠️ Usa RAM local
- ⚠️ Solo funciona cuando tu Mac está encendida

---

## 📊 Tabla Comparativa Resumida

| Proveedor | Modelo | Costo/1K fixes | Velocidad | Calidad ESP32 | Mejor Para |
|-----------|--------|----------------|-----------|---------------|------------|
| **Ollama** ⭐ | Qwen2.5 14B | **$0.00** | 2.8 tok/s | ⭐⭐⭐⭐⭐ | Desarrollo diario |
| **OpenAI** | GPT-4o-mini | $0.60 | 100 tok/s | ⭐⭐⭐⭐⭐ | Producción/CI |
| **OpenAI** | GPT-4o | $15.00 | 80 tok/s | ⭐⭐⭐⭐⭐ | Debugging complejo |
| **Anthropic** | Haiku 3.5 | $2.50 | 100 tok/s | ⭐⭐⭐⭐⭐ | Balance precio/calidad |
| **Anthropic** | Sonnet 3.5 | $20.00 | 70 tok/s | ⭐⭐⭐⭐⭐ | Proyectos críticos |
| **Azure** | GPT-4 | $18.00 | 80 tok/s | ⭐⭐⭐⭐⭐ | Empresas/SLA |

*Costos estimados para 1000 fixes por mes*

---

## 🎯 Recomendaciones por Caso de Uso

### 1. **Desarrollo Personal** (Tu caso actual)
```bash
🏆 RECOMENDACIÓN: Ollama (Local) - GRATIS
```

**Configuración actual:**
- ✅ Ya instalado: Qwen2.5-Coder 14B
- ✅ Ya probado: 71.4% éxito en stress test
- ✅ Costo: $0/mes

**Cuándo usar cloud:**
- Solo para casos muy complejos
- Cuando necesites máxima velocidad
- Para comparar calidad de respuestas

---

### 2. **Freelancer / Pequeña Empresa** (1-5 desarrolladores)
```bash
🏆 RECOMENDACIÓN: Hybrid (Local + GPT-4o-mini)
```

**Setup híbrido:**
1. **Desarrollo diario**: Ollama local (gratis)
2. **CI/CD pipeline**: GPT-4o-mini ($1-2/mes)
3. **Debugging crítico**: GPT-4o (pay-as-you-go)

**Costo estimado:** $2-5 USD/mes

---

### 3. **Empresa Mediana** (5-50 desarrolladores)
```bash
🏆 RECOMENDACIÓN: Claude 3.5 Haiku o GPT-4o-mini
```

**Razones:**
- Mayor throughput (muchos developers)
- SLA confiable
- API keys por proyecto
- Facturación centralizada

**Costo estimado:** $50-200 USD/mes (depende de uso)

---

### 4. **Empresa Grande / Enterprise**
```bash
🏆 RECOMENDACIÓN: Azure OpenAI + Ollama (híbrido)
```

**Razones:**
- SLA 99.9%
- Cumplimiento regulatorio (GDPR, SOC2)
- Residencia de datos en región específica
- Soporte empresarial 24/7
- Integración con Azure DevOps

**Costo:** Negociable con Microsoft (descuentos por volumen)

---

## 💳 Modelos de Facturación

### Pay-as-you-go (OpenAI, Anthropic)
```
✅ Pagas solo lo que usas
✅ Sin compromiso mensual
✅ Ideal para empezar
❌ Puede variar mes a mes
```

**Cómo funciona:**
1. Creas cuenta con tarjeta de crédito
2. Cada request consume tokens
3. Se cobra al final del mes
4. Puedes poner límites de gasto

**Límites de gasto recomendados:**
- Desarrollo: $5-10/mes
- Producción: $50-100/mes

### Enterprise/Volume (Azure, Anthropic Enterprise)
```
✅ Descuentos por volumen
✅ SLA garantizado
✅ Facturación mensual predecible
❌ Requiere compromiso anual
❌ Mínimos de gasto
```

**Típicamente:**
- Mínimo: $1,000-5,000/mes
- Descuentos: 20-40% vs pay-as-you-go
- Contrato: 12 meses

---

## 🔧 Configuración para Usar Cloud

### Opción 1: OpenAI (GPT-4o-mini) - MÁS ECONÓMICO

**Paso 1: Obtener API Key**
```bash
1. Ir a https://platform.openai.com/signup
2. Crear cuenta (gratis)
3. Agregar método de pago
4. Generar API key en https://platform.openai.com/api-keys
5. Copiar la key (sk-proj-...)
```

**Paso 2: Configurar en .env**
```bash
# Ya tienes esto configurado!
OPENAI_API_KEY=sk-proj-tu-api-key-aqui

# Cambiar provider
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

**Paso 3: Probar**
```bash
python3 agent/llm_provider.py
```

**Límite de gasto recomendado:** $5/mes (suficiente para 4000+ fixes)

---

### Opción 2: Anthropic (Claude 3.5 Haiku) - MEJOR CALIDAD

**Paso 1: Obtener API Key**
```bash
1. Ir a https://console.anthropic.com/
2. Crear cuenta
3. Agregar método de pago  
4. Generar API key
```

**Paso 2: Configurar en .env**
```bash
ANTHROPIC_API_KEY=sk-ant-tu-api-key-aqui
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-20241022
```

---

### Opción 3: Híbrido (Local + Cloud con fallback)

**La configuración más inteligente:**

```python
# En .env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5-coder:14b
LLM_FALLBACK_TO_LOCAL=false  # Cambiar a true para fallback

# También agregar (opcional)
OPENAI_API_KEY=sk-proj-...
```

**Comportamiento:**
1. ✅ Intenta primero con Ollama local (gratis)
2. ⚠️ Si falla o es muy lento → automáticamente usa OpenAI
3. 💰 Solo pagas cuando realmente lo necesitas

---

## 📈 Estimación de Costos Reales

### Escenario 1: Uso Ligero (Tú actualmente)
```
- 10 fixes por día
- 300 fixes por mes
- Modelo: GPT-4o-mini

Costo mensual: $0.18 - 0.36 USD
Costo anual: $2.16 - 4.32 USD
```

### Escenario 2: Desarrollo Activo
```
- 50 fixes por día
- 1500 fixes por mes
- Modelo: GPT-4o-mini

Costo mensual: $0.90 - 1.80 USD
Costo anual: $10.80 - 21.60 USD
```

### Escenario 3: CI/CD Pipeline
```
- 200 fixes por día (automated)
- 6000 fixes por mes
- Modelo: GPT-4o-mini

Costo mensual: $3.60 - 7.20 USD
Costo anual: $43.20 - 86.40 USD
```

### Escenario 4: Equipo de 10 Developers
```
- 500 fixes por día
- 15000 fixes por mes
- Modelo: Claude 3.5 Haiku

Costo mensual: $37.50 USD
Costo anual: $450 USD
```

---

## 🎁 Créditos Gratuitos Iniciales

### OpenAI
- 🆓 **$5 USD gratis** en nuevas cuentas
- ⏰ Válido por 3 meses
- 📊 Suficiente para **8000 fixes** con GPT-4o-mini

### Anthropic
- 🆓 **$5 USD gratis** en nuevas cuentas
- ⏰ Sin vencimiento (mientras uses)
- 📊 Suficiente para **2000 fixes** con Claude Haiku

### Azure
- 🆓 **$200 USD gratis** para nuevas cuentas
- ⏰ Válido por 30 días
- 📊 Suficiente para todo un mes de testing

---

## 🔐 Seguridad y Privacidad

### ⚠️ Datos enviados a la nube:
- ✅ Código con errores de compilación
- ✅ Mensajes de error del compilador
- ✅ Prompts de instrucciones

### ❌ Datos que NO se envían:
- ❌ Todo tu proyecto completo
- ❌ Archivos binarios
- ❌ Credenciales o secrets
- ❌ Variables de entorno

### 🛡️ Recomendaciones de seguridad:
1. ✅ Usa Ollama local para código propietario crítico
2. ✅ Sanitiza código antes de enviar a cloud (quita secrets)
3. ✅ Configura límites de gasto en cloud
4. ✅ Revisa ToS de cada provider sobre retención de datos

**Políticas de retención:**
- **OpenAI**: No entrena con tu API data (desde marzo 2023)
- **Anthropic**: No entrena con tu data
- **Azure**: Configurable (puede no almacenar nada)

---

## 🚀 Recomendación Final para Ti

### Para tu Mac Mini M4 con 16GB RAM:

```bash
🏆 SETUP RECOMENDADO: 95% Local + 5% Cloud

1. DIARIO: Usa Ollama local (gratis, privado, ya funciona)
2. EMERGENCIAS: Ten API key de OpenAI GPT-4o-mini ($0.60/mes)
3. COMPARACIÓN: Prueba ambos y decide

Costo esperado: $0-2 USD/mes
```

### Próximos pasos sugeridos:

1. **✅ Mantén Ollama como principal** (ya configurado)
2. **📝 Crea cuenta OpenAI** (obtén $5 gratis)
3. **🔑 Agrega API key a .env** (como backup)
4. **🧪 Prueba ambos en paralelo** (compara calidad)
5. **📊 Monitorea costos** (OpenAI dashboard)

---

## 📞 Soporte y Documentación

### OpenAI
- 📚 Docs: https://platform.openai.com/docs
- 💬 Support: https://help.openai.com/
- 📊 Usage: https://platform.openai.com/usage

### Anthropic
- 📚 Docs: https://docs.anthropic.com/
- 💬 Support: support@anthropic.com
- 📊 Usage: https://console.anthropic.com/usage

### Azure OpenAI
- 📚 Docs: https://learn.microsoft.com/azure/ai-services/openai/
- 💬 Support: Azure Portal
- 📊 Usage: Azure Cost Management

---

**Última actualización**: 29 de octubre de 2025  
**Precios**: Verificados en octubre 2025 (pueden variar)  
**Configuración actual**: Ollama Qwen2.5-Coder 14B (Local, Gratis)
