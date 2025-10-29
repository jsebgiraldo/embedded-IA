# Guía Rápida: MCP Server

## 🚀 Inicio rápido

### 1. Levantar servicios
```bash
# Levantar todos los contenedores
docker compose up -d

# Solo MCP server
docker compose up -d mcp-server

# Solo desarrollo
docker compose up -d dev
```

### 2. Usar agente con MCP

**Modo interactivo:**
```bash
docker compose exec dev python3 /agent/agent_mcp.py
```

**Comando único:**
```bash
docker compose exec dev python3 /agent/agent_mcp.py "Compila el proyecto"
```

### 3. Comandos útiles

```bash
# Ver logs del MCP server
docker compose logs -f mcp-server

# Entrar al contenedor MCP
docker compose exec mcp-server bash

# Instalar/actualizar MCP server
docker compose exec mcp-server bash -lc "cd /mcp-server && pip install -e ."

# Probar herramienta directamente
docker compose exec mcp-server python3 -c "
from mcp_idf.tools import IDFTools
tools = IDFTools()
result = tools.doctor()
print(result)
"
```

## 🔧 Ejemplos de queries

### Compilación y diagnóstico
```
"Compila el proyecto y dime qué errores hay"
"Ejecuta doctor para verificar el entorno"
"Muestra el tamaño del firmware compilado"
```

### Gestión de archivos
```
"Lee el archivo main/main.c"
"Lista todos los archivos en el directorio main"
"Crea un nuevo archivo main/hello.c con un programa básico"
```

### Target y configuración
```
"Cambia el target a esp32s3"
"Limpia los artefactos de compilación"
"Configura el proyecto para esp32c6"
```

### Workflow completo
```
"Compila el proyecto, si hay errores léeme el main.c, 
analiza los errores y propón una corrección"
```

## 🏗️ Arquitectura

```
Usuario → Agent (GPT-4) → MCP Client → MCP Tools → ESP-IDF
```

1. **Usuario**: Escribe query en lenguaje natural
2. **Agent**: LLM decide qué herramientas usar
3. **MCP Client**: Traduce llamadas a protocolo MCP
4. **MCP Tools**: Ejecutan comandos reales
5. **Resultado**: Vuelve al usuario

## 📝 Diferencia con agente básico

### Agente básico (`agent.py`)
- ❌ Herramientas acopladas al agente
- ❌ Difícil de testear
- ❌ No escalable

### Agente MCP (`agent_mcp.py`)
- ✅ Herramientas desacopladas
- ✅ Fácil de testear y mantener
- ✅ Escalable (local, remoto, CI)
- ✅ API estable

## 🔍 Debug

### Ver qué herramientas tiene el agente
```bash
docker compose exec dev python3 -c "
from mcp_idf.client import MCPClient
client = MCPClient()
tools = client.get_langchain_tools()
for tool in tools:
    print(f'- {tool.name}: {tool.description}')
"
```

### Probar herramienta individual
```python
from mcp_idf.tools import IDFTools

tools = IDFTools()

# Compilar
result = tools.build()
print(result)

# Cambiar target
result = tools.set_target("esp32s3")
print(result)
```

## 🆘 Problemas comunes

### "OPENAI_API_KEY not found"
```bash
# Verificar que .env existe
cat .env

# Reiniciar contenedor
docker compose restart dev
```

### "Module mcp_idf not found"
```bash
# Reinstalar MCP server
docker compose exec dev bash -lc "cd /mcp-server && pip install -e ."
```

### Device not found (/dev/ttyUSB0)
```bash
# En macOS, ajustar docker-compose.yml
devices:
  - /dev/cu.usbserial-XXX:/dev/ttyUSB0
```

## 📚 Más info

- [README principal](../README.md)
- [MCP Server README](README.md)
- [MCP Spec](https://spec.modelcontextprotocol.io/)
