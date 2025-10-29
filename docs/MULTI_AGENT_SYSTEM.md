# 🚀 ESP32 Multi-Agent Development System

## 📋 Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Arquitectura de Agentes](#arquitectura-de-agentes)
3. [Workflow y Paralelización](#workflow-y-paralelización)
4. [MCP Tools Disponibles](#mcp-tools-disponibles)
5. [Feedback Loop QA](#feedback-loop-qa)
6. [Guía de Uso](#guía-de-uso)
7. [Ejemplos](#ejemplos)

---

## Visión General

Sistema multi-agente para desarrollo ESP32 que coordina roles especializados para maximizar eficiencia mediante paralelización y feedback loops automáticos.

### 🎯 Objetivos
- ✅ **Paralelización máxima**: Flash + QEMU + Diagnósticos simultáneos
- ✅ **Feedback automático**: QA detecta fallos → Developer corrige → Re-test
- ✅ **Cache de artefactos**: Build una vez, flash múltiples veces (ahorra 2-3 min)
- ✅ **Roles especializados**: Cada agente tiene herramientas y responsabilidades específicas

### 🏗️ Componentes Principales

```
agent/
├── orchestrator.py       # Coordinador multi-agente con paralelización
├── demo_workflow.py      # Demo completa del workflow
└── app/tools/           # Herramientas de LangChain

mcp-server/
└── src/mcp_idf/
    ├── client.py        # 15 LangChain tools
    ├── server.py        # MCP server (stdio)
    └── tools/
        ├── idf_commands.py      # ESP-IDF wrapper
        ├── artifact_manager.py  # Build cache con SHA256
        ├── qemu_manager.py      # QEMU lifecycle
        └── file_manager.py      # File operations
```

---

## Arquitectura de Agentes

### 🎭 Roles y Responsabilidades

#### 1. **Project Manager** 🎯
**Objetivo**: Coordinar workflow, importar/validar proyectos

**Tools**:
- `list_files` - Listar estructura del proyecto
- `read_source_file` - Leer archivos fuente
- `idf_set_target` - Configurar chip target

**Responsabilidades**:
- Validar estructura del proyecto (CMakeLists.txt, main/, etc.)
- Configurar target chip (esp32, esp32c6, etc.)
- Coordinar fases del workflow
- Importar proyectos de GitHub

**Flujo**:
```
GitHub URL → Clone → Validate Structure → Set Target → Next Phase
```

---

#### 2. **Developer** 👨‍💻
**Objetivo**: Crear/modificar código, corregir bugs reportados por QA

**Tools**:
- `read_source_file` - Leer código fuente
- `write_source_file` - Escribir/modificar código
- `list_files` - Navegar proyecto

**Responsabilidades**:
- Implementar nuevas features
- Corregir bugs detectados por QA
- Refactorizar código
- Aplicar fixes automáticos o asistidos por LLM

**Feedback Loop**:
```
QA Report → Analyze Issues → Generate Fix → Write Code → Trigger Rebuild
```

---

#### 3. **Builder** 🔨
**Objetivo**: Compilar firmware y gestionar artefactos

**Tools**:
- `idf_build` - Compilar firmware
- `idf_clean` - Limpiar build
- `idf_size` - Análisis de tamaño
- `get_build_artifacts` - Obtener artefactos cached

**Responsabilidades**:
- Compilar firmware con optimizaciones
- Guardar artefactos con SHA256 checksum
- Generar reportes de tamaño
- Proveer binarios para flash/QEMU

**Artifact Cache**:
```
Build → Save to .artifacts_cache/ → SHA256 → Metadata JSON
Flash/QEMU → Check cache → Use if valid → Skip rebuild
```

**Tiempo ahorrado**: 2-3 minutos por flash con cache hit

---

#### 4. **Tester** 🧪
**Objetivo**: Ejecutar tests en hardware y simulación (PARALELO)

**Tools**:
- `idf_flash` - Flash a hardware
- `run_qemu_simulation` - Iniciar QEMU
- `stop_qemu_simulation` - Detener QEMU
- `qemu_simulation_status` - Estado de QEMU
- `qemu_get_output` - Capturar output

**Responsabilidades**:
- Flash a ESP32 físico (paralelo con QEMU)
- Ejecutar simulación QEMU (paralelo con flash)
- Capturar outputs de consola
- Reportar resultados de ambos tests

**Paralelización**:
```
Build Complete
    ├─> [PARALLEL] Flash to ESP32-C6 (port: /dev/cu.usbmodem21101)
    └─> [PARALLEL] QEMU Simulation (idf.py qemu)
           ↓
    Both complete → Next Phase
```

**Benefit**: Ejecuta flash + QEMU simultáneamente (~30 segundos cada uno)

---

#### 5. **Doctor** 🏥
**Objetivo**: Diagnóstico de hardware y ambiente

**Tools**:
- `idf_doctor` - Diagnóstico ESP-IDF
- `qemu_inspect_state` - Inspeccionar estado QEMU

**Responsabilidades**:
- Validar configuración ESP-IDF
- Verificar conectividad de hardware
- Inspeccionar estado interno QEMU
- Reportar problemas de ambiente

**Checks**:
- Python version y dependencies
- ESP-IDF tools instalados
- Serial port disponible
- QEMU registers y memory state

---

#### 6. **QA** ✅
**Objetivo**: Validar resultados y detectar fallos

**Tools**:
- `qemu_get_output` - Analizar output QEMU
- `read_source_file` - Revisar código
- `list_files` - Inspeccionar estructura
- `idf_size` - Validar uso de memoria

**Responsabilidades**:
- Analizar outputs de tests
- Detectar errores/warnings
- Validar comportamientos esperados
- Reportar issues a Developer con contexto
- Aprobar o rechazar build

**Análisis**:
```python
# QA checks realizados
checks = {
    "build_success": "No errors en compilación",
    "expected_output": "'Hello World' presente en QEMU",
    "no_runtime_errors": "Sin 'abort' o 'error' en logs",
    "memory_usage": "Free heap > threshold",
    "flash_size": "Binary size < partition size"
}
```

**Feedback a Developer**:
```json
{
  "passed": false,
  "issues": [
    {
      "severity": "high",
      "component": "application",
      "message": "Expected 'Hello World' output not found in QEMU",
      "fix_suggestion": "Check printf() in main/main.c"
    }
  ]
}
```

---

## Workflow y Paralelización

### 📊 Fases del Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Project Setup (Sequential)                             │
├─────────────────────────────────────────────────────────────────┤
│ [Project Manager] Validate Structure                            │
│          ↓                                                       │
│ [Project Manager] Set Target (esp32, esp32c6, etc.)            │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Build (Sequential)                                     │
├─────────────────────────────────────────────────────────────────┤
│ [Builder] Compile Firmware                                      │
│          ↓                                                       │
│ [Builder] Cache Artifacts (SHA256)                              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Testing (PARALLEL ⚡)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌─────────────────────────┐  ┌─────────────────────────┐   │
│    │ [Tester] Flash Device    │  │ [Tester] QEMU Simulation│   │
│    │ - Use cached artifacts   │  │ - idf.py qemu           │   │
│    │ - /dev/cu.usbmodem21101 │  │ - Capture console       │   │
│    └─────────────────────────┘  └─────────────────────────┘   │
│                   ↓                         ↓                   │
│              Flash Output              QEMU Output              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Validation (PARALLEL ⚡)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌─────────────────────────┐  ┌─────────────────────────┐   │
│    │ [Doctor] Diagnostics     │  │ [QA] Analyze Results    │   │
│    │ - idf_doctor             │  │ - Check build           │   │
│    │ - Hardware checks        │  │ - Validate outputs      │   │
│    │ - QEMU state inspection  │  │ - Detect issues         │   │
│    └─────────────────────────┘  └─────────────────────────┘   │
│                   ↓                         ↓                   │
│            Diagnostics Report         QA Report                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                          ↓
                    ┌──────────┐
                    │ QA PASS? │
                    └──────────┘
                     /          \
                  YES            NO
                   ↓              ↓
            ┌──────────┐   ┌─────────────────────────────────┐
            │ Complete │   │ PHASE 5: Feedback Loop (QA->Dev)│
            └──────────┘   ├─────────────────────────────────┤
                           │ [Developer] Analyze Issues       │
                           │          ↓                       │
                           │ [Developer] Generate Fixes       │
                           │          ↓                       │
                           │ [Builder] Rebuild                │
                           │          ↓                       │
                           │ [QA] Re-analyze                  │
                           │          ↓                       │
                           │ Iteration < Max? → Repeat/Done   │
                           └─────────────────────────────────┘
```

### ⚡ Puntos de Paralelización

1. **Testing Phase**: Flash + QEMU ejecutan simultáneamente
   - Ambos usan los mismos cached artifacts
   - No hay dependencias entre ellos
   - Ahorra ~30 segundos

2. **Validation Phase**: Doctor + QA ejecutan simultáneamente
   - Doctor verifica hardware/ambiente
   - QA analiza outputs de tests
   - Independientes entre sí
   - Ahorra ~10-15 segundos

3. **Futuras optimizaciones**:
   - Múltiples tests QEMU con diferentes configs (parallel)
   - Static analysis tools (linting, security scans) en parallel
   - Multiple device flashing si hay varios boards conectados

### 🔄 Feedback Loop (QA → Developer)

**Trigger**: QA detecta issues (tests fail, unexpected behavior)

**Proceso**:
1. QA genera reporte detallado con issues
2. Developer recibe contexto: código afectado, error logs, sugerencias
3. Developer genera fix (automático o LLM-asistido)
4. Builder recompila firmware
5. Tester re-ejecuta tests
6. QA re-analiza resultados
7. Repeat hasta max iterations (default: 3) o success

**Ejemplo de issue**:
```json
{
  "severity": "high",
  "component": "application",
  "file": "main/main.c",
  "line": 42,
  "message": "Expected 'Hello World' not found in output",
  "context": {
    "expected": "Hello World! Counter: 0",
    "actual": "Starting application..."
  },
  "fix_suggestion": "Check printf() call in app_main()"
}
```

---

## MCP Tools Disponibles

### 📦 15 LangChain Tools

#### Build & Compile
1. **`idf_build`** - Compilar proyecto ESP-IDF
   - Output: Build logs, errors, warnings
   - Side effect: Guarda artifacts en cache

2. **`idf_clean`** - Limpiar build artifacts
   - Útil antes de full rebuild

3. **`idf_size`** - Análisis de tamaño del firmware
   - Muestra uso de flash/RAM por componente

4. **`get_build_artifacts`** - Obtener info de cached artifacts
   - Retorna: binarios, checksums, metadata

#### Flash & Deploy
5. **`idf_flash`** - Flash firmware a device
   - Parámetros: `port`, `use_cached` (default: True)
   - Con cache: Usa binarios cached, no rebuild

6. **`idf_set_target`** - Configurar chip target
   - Valores: esp32, esp32s2, esp32s3, esp32c3, esp32c6, esp32h2

#### QEMU Simulation
7. **`run_qemu_simulation`** - Iniciar simulación QEMU
   - Usa `idf.py qemu` (ESP-IDF 6.1+)
   - Console output completo disponible

8. **`stop_qemu_simulation`** - Detener simulación

9. **`qemu_simulation_status`** - Estado de QEMU
   - PID, CPU%, memoria, uptime

10. **`qemu_get_output`** - Capturar console output
    - Parámetro: `lines` (default: 50)
    - Útil para QA analysis

11. **`qemu_inspect_state`** - Inspeccionar estado interno
    - Comandos: `info registers`, `info mem`, `info mtree`
    - Para debugging avanzado

#### Diagnostics
12. **`idf_doctor`** - Diagnóstico completo ESP-IDF
    - Python version, dependencies, tools, paths

#### File Operations
13. **`read_source_file`** - Leer archivo fuente
    - Path relativo desde workspace root

14. **`write_source_file`** - Escribir/modificar archivo
    - Para Developer fixes

15. **`list_files`** - Listar directorio
    - Útil para Project Manager validation

---

## Guía de Uso

### 🚀 Inicio Rápido

#### 1. Setup Inicial
```bash
cd /Users/sebastiangiraldo/Documents/embedded-IA

# Levantar containers
docker compose up -d

# Verificar MCP server
docker compose exec mcp-server bash -lc "which idf.py"
```

#### 2. Ejecutar Demo Workflow
```bash
# Desde host
cd agent
python3 demo_workflow.py

# Desde container (recommended)
docker compose exec mcp-server python3 /agent/demo_workflow.py
```

#### 3. Usar Orchestrator en tu código
```python
from mcp_idf.client import MCPClient
from agent.orchestrator import AgentOrchestrator

# Initialize
client = MCPClient()
tools = client.get_langchain_tools()
orchestrator = AgentOrchestrator(tools)

# Run workflow
results = await orchestrator.execute_workflow(
    project_path="/workspace",
    target="esp32c6",
    flash_device=True,      # Flash to real hardware
    run_qemu=True           # Also run simulation
)

# Check results
if results["success"]:
    print("✅ All phases completed!")
else:
    print(f"❌ Failed with {len(results['phases'])} issues")
```

### 🔧 Configuración

#### Orchestrator Options
```python
orchestrator = AgentOrchestrator(
    langchain_tools=tools,
    max_qa_iterations=3,     # Max feedback loops
    enable_parallel=True,    # Enable parallelization
    timeout_per_task=300     # Task timeout (seconds)
)
```

#### Workflow Parameters
```python
results = await orchestrator.execute_workflow(
    project_path="/workspace",           # ESP-IDF project path
    target="esp32c6",                    # Target chip
    flash_device=True,                   # Enable hardware flash
    run_qemu=True,                       # Enable QEMU simulation
    flash_port="/dev/cu.usbmodem21101", # Serial port
    qemu_timeout=30                      # QEMU run time (seconds)
)
```

### 📊 Monitorear Workflow

#### Real-time Progress
El orchestrator imprime updates en tiempo real:
```
🚀 Executing [project_manager] validate_project_structure (task: setup_project)
✅ Completed [project_manager] validate_project_structure

🚀 Executing [builder] compile_and_cache (task: build_firmware)
✅ Completed [builder] compile_and_cache

🚀 Executing [tester] flash_to_hardware (task: flash_device)
🚀 Executing [tester] start_qemu (task: run_simulation)
✅ Completed [tester] flash_to_hardware
✅ Completed [tester] start_qemu
```

#### Workflow Summary
```python
# Get summary after execution
summary = orchestrator.get_workflow_summary()
print(summary)
```

Output:
```
╔══════════════════════════════════════════════════════════════╗
║             ESP32 Development Workflow Summary               ║
╚══════════════════════════════════════════════════════════════╝

📁 Project: /workspace
🎯 Target: esp32c6
🔄 QA Iterations: 1/3

Tasks:
  ✅ [project_manager] validate_project_structure
  ✅ [project_manager] set_chip_target
  ✅ [builder] compile_and_cache
  ✅ [tester] flash_to_hardware
  ✅ [tester] start_qemu
  ✅ [doctor] run_diagnostics
  ❌ [qa] analyze_results
  ✅ [developer] fix_issues
  ✅ [builder] compile_and_cache
  ✅ [qa] analyze_results
```

---

## Ejemplos

### Ejemplo 1: Workflow Completo (Hello World)

```python
import asyncio
from mcp_idf.client import MCPClient
from agent.orchestrator import AgentOrchestrator

async def hello_world_workflow():
    # Setup
    client = MCPClient()
    tools = client.get_langchain_tools()
    orchestrator = AgentOrchestrator(tools)
    
    # Execute
    results = await orchestrator.execute_workflow(
        project_path="/workspace",
        target="esp32",
        flash_device=False,  # Only QEMU for demo
        run_qemu=True
    )
    
    # Analyze QEMU output
    if "qemu_output" in results["artifacts"]:
        output = results["artifacts"]["qemu_output"]
        
        # QA checks
        if "Hello World" in output:
            print("✅ QA: Hello World message found!")
        else:
            print("❌ QA: Expected output not found")
    
    return results

# Run
asyncio.run(hello_world_workflow())
```

### Ejemplo 2: Flash con Cache (Rápido)

```python
# Primera vez: build completo (~2-3 min)
results1 = await orchestrator.execute_workflow(
    project_path="/workspace",
    target="esp32c6",
    flash_device=True,
    run_qemu=False
)

# Segunda vez: usa cache (~30 sec)
# Modifica algo que no afecta binarios
results2 = await orchestrator.execute_workflow(
    project_path="/workspace",
    target="esp32c6",
    flash_device=True,
    run_qemu=False
)
# ✅ Flash usa cached artifacts, no rebuild!
```

### Ejemplo 3: Feedback Loop (QA → Developer)

```python
async def test_with_qa_feedback():
    orchestrator = AgentOrchestrator(
        tools,
        max_qa_iterations=3  # Allow up to 3 fix attempts
    )
    
    # Introduce a bug first
    developer = tools["write_source_file"]
    developer.invoke({
        "path": "main/main.c",
        "content": '// Bug: missing printf()\nvoid app_main() {}'
    })
    
    # Run workflow - QA will catch missing output
    results = await orchestrator.execute_workflow(
        project_path="/workspace",
        target="esp32",
        flash_device=False,
        run_qemu=True
    )
    
    # Check if QA triggered feedback loop
    if results["qa_iterations"] > 0:
        print(f"🔄 QA triggered {results['qa_iterations']} fix iterations")
        
        # Developer should have applied fixes
        for iteration in range(results["qa_iterations"]):
            print(f"   Iteration {iteration+1}: Fix applied")
    
    # Final result
    if results["success"]:
        print("✅ All issues resolved!")
    else:
        print(f"❌ Failed after {results['qa_iterations']} attempts")
    
    return results

asyncio.run(test_with_qa_feedback())
```

### Ejemplo 4: Paralelización Máxima

```python
async def parallel_workflow():
    """
    Ejecuta:
    - Flash a hardware
    - QEMU simulation
    - Doctor diagnostics
    - QA analysis
    Todo en paralelo donde sea posible
    """
    orchestrator = AgentOrchestrator(tools)
    
    # Enable all parallel tasks
    results = await orchestrator.execute_workflow(
        project_path="/workspace",
        target="esp32c6",
        flash_device=True,   # Parallel task 1
        run_qemu=True        # Parallel task 2
        # Doctor y QA también corren en paralelo después
    )
    
    # Timing info
    total_time = sum(
        task.timestamp for task in orchestrator.state.tasks.values()
        if task.status == TaskStatus.COMPLETED
    )
    
    print(f"⚡ Total execution time: {total_time}s")
    print(f"   (Sequential would be ~2x longer)")
    
    return results
```

### Ejemplo 5: Import desde GitHub

```python
async def github_import_workflow():
    """
    Import project from GitHub and run full workflow
    """
    # Project Manager role: import project
    pm_tools = ["list_files", "read_source_file", "idf_set_target"]
    
    # 1. Clone repo (manual or via subprocess)
    import subprocess
    subprocess.run([
        "git", "clone",
        "https://github.com/espressif/esp-idf-template.git",
        "/workspace/imported_project"
    ])
    
    # 2. Validate structure
    client = MCPClient()
    tools = client.get_langchain_tools()
    list_tool = tools["list_files"]
    
    files = list_tool.invoke("/workspace/imported_project")
    if "CMakeLists.txt" not in files:
        print("❌ Invalid ESP-IDF project structure")
        return
    
    # 3. Run workflow on imported project
    orchestrator = AgentOrchestrator(tools)
    results = await orchestrator.execute_workflow(
        project_path="/workspace/imported_project",
        target="esp32",
        flash_device=True,
        run_qemu=True
    )
    
    print(f"✅ Imported and tested GitHub project")
    return results
```

---

## 📈 Performance Optimizations

### Build Cache
- **First build**: ~120-180 seconds
- **Subsequent flashes**: ~30 seconds (using cache)
- **Savings**: 2-3 minutes per flash

### Parallel Execution
- **Sequential**: Flash (30s) + QEMU (30s) + Doctor (10s) + QA (10s) = **80s**
- **Parallel**: max(Flash, QEMU) + max(Doctor, QA) = **40s**
- **Savings**: 50% time reduction

### QA Feedback Loop
- **Without loop**: Build → Test → Manual fix → Rebuild → Retest = **10+ min**
- **With loop**: Automated fix → Rebuild → Retest = **5 min**
- **Savings**: 5+ minutes + developer time

---

## 🔮 Próximos Pasos

### Fase 2: Integraciones
- [ ] GitHub Actions para CI/CD
- [ ] Integration con LLM para Developer fixes inteligentes
- [ ] Web UI para monitoring de workflows
- [ ] Slack/Discord notifications de QA failures

### Fase 3: Advanced Features
- [ ] Multi-device testing (flash a múltiples boards)
- [ ] Performance profiling automático
- [ ] Security scans (CVE checks, static analysis)
- [ ] Code coverage reports con QEMU

### Fase 4: Productización
- [ ] REST API para orchestrator
- [ ] Database para workflow history
- [ ] Role-based access control
- [ ] Métricas y analytics dashboard

---

## 📚 Referencias

- [ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/)
- [QEMU ESP32 Support](https://github.com/espressif/qemu)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)

---

## 🤝 Contribuir

Este sistema está en desarrollo activo. Áreas donde puedes contribuir:

1. **Nuevos agentes**: Profiler, Security Scanner, etc.
2. **Optimizaciones**: Más puntos de paralelización
3. **Integraciones**: GitHub, GitLab, Jenkins, etc.
4. **Testing**: Unit tests, integration tests
5. **Documentation**: Más ejemplos, tutoriales

---

**Versión**: 1.0.0  
**Última actualización**: Octubre 28, 2025  
**Autor**: Sebastian Giraldo  
**License**: MIT
