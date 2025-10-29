# MCP Server for ESP-IDF

**Model Context Protocol (MCP) Server** para interactuar con el toolchain ESP-IDF de forma desacoplada y escalable.

## 🎯 Arquitectura

```
┌─────────────────┐
│  Agent (Brain)  │  ← LangChain + LLM (GPT-4)
└────────┬────────┘
         │ MCP Protocol
         ├─────────────────────────────────┐
         │                                 │
┌────────▼────────┐            ┌──────────▼─────────┐
│  IDF Commands   │            │   File Manager     │
│  - build        │            │   - read_file      │
│  - flash        │            │   - write_file     │
│  - monitor      │            │   - list_dir       │
│  - set_target   │            │   - file_info      │
│  - clean        │            │                    │
│  - size         │            │                    │
│  - doctor       │            │                    │
└─────────────────┘            └────────────────────┘
```

## 🚀 Herramientas disponibles

### Comandos ESP-IDF

- **build**: Compila el proyecto con `idf.py build`
- **flash**: Flashea firmware al dispositivo
- **monitor**: Inicia monitor serial (retorna comando)
- **set_target**: Configura target chip (esp32, esp32s3, etc.)
- **clean**: Limpia artefactos de compilación
- **size**: Muestra información de tamaño del binario
- **doctor**: Ejecuta diagnósticos del entorno

### Gestión de archivos

- **read_file**: Lee un archivo del workspace
- **write_file**: Escribe contenido en un archivo
- **list_directory**: Lista contenido de un directorio
- **file_info**: Obtiene información detallada de un archivo

## 📦 Instalación

El MCP server se instala automáticamente en el contenedor:

```bash
docker compose up -d mcp-server
```

## 🔧 Uso

### Modo standalone (servidor MCP)

```bash
docker compose exec mcp-server python3 -m mcp_idf.server
```

### Modo cliente (desde el agente)

```python
from mcp_idf.client import MCPClient

# Crear cliente
mcp_client = MCPClient()

# Obtener herramientas para LangChain
tools = mcp_client.get_langchain_tools()

# Usar con agente
agent = initialize_agent(tools, llm, agent_type="zero-shot-react-description")
```

### Ejecutar agente con MCP

```bash
# Modo interactivo
docker compose exec dev python3 /agent/agent_mcp.py

# Comando único
docker compose exec dev python3 /agent/agent_mcp.py "Compila el proyecto y muéstrame los errores"
```

## 🏗️ Estructura del proyecto

```
mcp-server/
├── pyproject.toml           # Configuración del paquete
├── src/
│   └── mcp_idf/
│       ├── __init__.py
│       ├── server.py        # Servidor MCP principal
│       ├── client.py        # Cliente MCP para LangChain
│       └── tools/
│           ├── __init__.py
│           ├── idf_commands.py    # Herramientas ESP-IDF
│           └── file_manager.py    # Gestión de archivos
```

## 🎨 Ventajas del MCP

1. **Desacoplamiento**: El agente (cerebro) no conoce los detalles de implementación
2. **Escalabilidad**: Fácil agregar nuevas herramientas sin modificar el agente
3. **Portabilidad**: Las herramientas pueden ejecutarse local, remoto o en CI
4. **Testabilidad**: Tools y agente se prueban independientemente
5. **Versionado**: API estable entre agente y herramientas

## 🔄 Flujo de trabajo

```
Usuario → Agente (LLM) → MCP Client → MCP Server → IDF Tools
   ↑                                                     ↓
   └─────────────── Resultado ←─────────────────────────┘
```

## 📝 Ejemplo de uso

```python
# El agente decide qué herramientas usar basándose en el query
query = "Compila el proyecto, y si hay errores en main.c, corrígelos"

# El agente ejecutará:
# 1. idf_build() → detecta errores
# 2. read_source_file("main/main.c") → lee el archivo
# 3. Analiza errores con LLM
# 4. write_source_file("main/main.c|<código corregido>") → corrige
# 5. idf_build() → verifica que compile
```

## 🚦 Targets soportados

- esp32
- esp32s2
- esp32s3
- esp32c3
- esp32c6
- esp32h2

## 🔐 Seguridad

- **Path validation**: Solo acceso a archivos dentro del workspace
- **Timeouts**: Comandos con timeout de 5 minutos
- **Error handling**: Manejo robusto de errores

## 📚 Más información

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
