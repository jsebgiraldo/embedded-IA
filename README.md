# 🤖 ESP32 Multi-Agent Development System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ESP-IDF](https://img.shields.io/badge/ESP--IDF-v6.1-blue.svg)](https://github.com/espressif/esp-idf)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> **AI-powered multi-agent orchestration system for ESP32 firmware development with intelligent caching, parallel execution, and automated QA feedback loops.**

Transform your ESP32 development workflow with specialized AI agents that coordinate build, test, and validation tasks—achieving up to 83% faster deployment cycles through smart artifact caching and parallel execution.

---

## 🌟 Key Features

### 🎭 **6 Specialized Agents**
- **🎯 Project Manager** - Project setup, validation, and coordination
- **👨‍💻 Developer** - Code writing and automated bug fixing
- **🔨 Builder** - Optimized compilation with SHA256 artifact caching
- **🧪 Tester** - Parallel hardware flashing + QEMU simulation
- **🏥 Doctor** - Hardware diagnostics and environment validation
- **✅ QA** - Automated validation with intelligent feedback loops

### ⚡ **Performance Optimizations**
- **83% faster** flash operations via build cache (3 min → 30 sec)
- **50% faster** testing phase through parallel execution
- **2-3 minutes saved** per flash with cache hits
- **Automatic retry** up to 3 iterations for QA-detected issues

### 🛠️ **Model Context Protocol (MCP) Integration**
- 15 specialized tools for ESP-IDF operations
- LangChain integration for extensibility
- Decoupled tool architecture for easy testing
- Support for local and remote tool execution

### 🎮 **QEMU Integration**
- Full ESP32 simulation without hardware
- Console output capture for debugging
- Monitor commands for register inspection
- Perfect for CI/CD pipelines

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [System Architecture](#-system-architecture)
- [Performance Metrics](#-performance-metrics)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Development](#-development)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- macOS/Linux (Windows via WSL2)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/esp32-multi-agent.git
cd esp32-multi-agent

# Copy environment template
cp .env.example .env

# Edit .env with your settings (ESP32 target, serial port, etc.)
nano .env
```

### 2. Start Services

```bash
# Start Docker containers
docker compose up -d

# Verify services are running
docker compose ps
```

### 3. Run Your First Workflow

```bash
# Simple workflow demonstration
python3 demo_workflow_simple.py

# Visual architecture viewer
python3 show_architecture.py
```

### 4. Build & Flash Example Project

```bash
# Enter development container
docker compose exec dev bash

# Inside container:
cd /workspace
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   User / LLM Interface                       │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              Agent Orchestrator (AsyncIO)                    │
│  • Task Dependency Management                                │
│  • Parallel Execution Engine                                 │
│  • QA Feedback Loop Controller                               │
└─────┬──────┬──────┬──────┬──────┬──────────────────────────┘
      │      │      │      │      │
   ┌──┴──┐┌──┴──┐┌──┴──┐┌──┴──┐┌──┴──┐
   │ PM  ││ DEV ││ BLD ││ TST ││ DOC │
   │ 🎯  ││ 👨‍💻 ││ 🔨 ││ 🧪 ││ 🏥  │
   └──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘
      └──────┴──────┴──────┴──────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────┐         ┌──────────┐
    │ MCP     │         │ Build    │
    │ Tools   │         │ Cache    │
    │ (15)    │         │ (SHA256) │
    └────┬────┘         └──────────┘
         │
    ┌────┴─────────┐
    │   ESP-IDF    │
    │   v6.1       │
    └──────────────┘
```

### Workflow Execution Flow

```
Setup (sequential) → Build (sequential) → Testing (parallel) → Validation (parallel)
                                               ↓                       ↓
                                          Flash + QEMU         Doctor + QA
                                          (simultaneous)       (simultaneous)
                                               ↓                       ↓
                                          30 seconds              10 seconds
                                          (vs 60s seq)           (vs 20s seq)
```

**[See full architecture diagram →](docs/ARCHITECTURE.md)**

---

## 📊 Performance Metrics

### Build Cache Impact

| Operation | Without Cache | With Cache | Improvement |
|-----------|--------------|------------|-------------|
| Flash firmware | 3 min | 30 sec | **83% faster** 🔥 |
| Full workflow | 7 min | 3 min | **57% faster** 🔥 |
| Testing phase | 60 sec | 30 sec | **50% faster** ⚡ |

### Parallelization Gains

```
Sequential Workflow:    PM → Dev → Build → Flash → QEMU → Doctor → QA
Time:                   ~7 minutes

Parallel Workflow:      PM → Dev → Build → [Flash || QEMU] → [Doctor || QA]
Time:                   ~3 minutes (with cache)

Savings:                57% faster
```

### Real-World Scenarios

1. **First build** (no cache): 6 min → 14% improvement over manual
2. **Rebuild with cache**: 3 min → 57% improvement
3. **Flash only** (cached): 30 sec → 83% improvement
4. **CI/CD pipeline**: ~2 min (QEMU only, no hardware)

---

## 💻 Usage Examples

### Example 1: Simple Build and Flash

```bash
# Using Docker
docker compose exec mcp-server bash -lc "cd /workspace && idf.py build flash"
```

### Example 2: QEMU Simulation

```bash
# Start QEMU simulation
docker compose exec mcp-server bash -lc "cd /workspace && idf.py qemu"

# In another terminal, get console output
docker compose exec mcp-server python3 -c "
from mcp_idf.tools.qemu_manager import QEMUManager
qemu = QEMUManager()
print(qemu.get_output(lines=50))
"
```

### Example 3: Multi-Agent Workflow (Python API)

```python
import asyncio
from mcp_idf.client import MCPClient
from agent.orchestrator import AgentOrchestrator

async def main():
    # Initialize MCP client and get tools
    client = MCPClient()
    tools = client.get_langchain_tools()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(tools)
    
    # Execute workflow with QEMU testing
    results = await orchestrator.execute_workflow(
        project_path="/workspace",
        target="esp32c6",
        flash_device=False,  # Use False for CI/CD
        run_qemu=True
    )
    
    print(f"Success: {results['success']}")
    print(f"QA Iterations: {results['qa_iterations']}")
    
asyncio.run(main())
```

### Example 4: Test Artifact Caching

```bash
# First build (no cache)
./test_flash_cached.sh

# Second build (with cache) - should be ~2-3 min faster
./test_flash_cached.sh
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` to configure your setup:

```bash
# Target chip
ESP_IDF_TARGET=esp32c6  # esp32, esp32s2, esp32s3, esp32c3, esp32c6, esp32h2

# Serial port (adjust for your system)
SERIAL_PORT=/dev/cu.usbmodem21101  # macOS
# SERIAL_PORT=/dev/ttyUSB0         # Linux

# Optional: QEMU settings
QEMU_TIMEOUT=300  # seconds
```

### Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  dev:
    volumes:
      - ./my-custom-workspace:/custom-workspace
    environment:
      - MY_CUSTOM_VAR=value
```

### Agent Configuration

Customize agent behavior in `agent/orchestrator.py`:

```python
class AgentOrchestrator:
    def __init__(self, tools: List):
        # ... 
        self.max_qa_iterations = 3  # Adjust feedback loop limit
        self.parallel_enabled = True  # Enable/disable parallelization
```

---

## 🛠️ Development

### Project Structure

```
esp32-multi-agent/
├── agent/                      # Multi-agent orchestrator
│   ├── orchestrator.py         # Main coordinator (690 lines)
│   ├── demo_workflow.py        # Usage example
│   └── app/
│       └── tools/              # Specialized tools
│           ├── artifacts_manager.py  # Build cache
│           └── qemu_manager.py       # QEMU lifecycle
├── mcp-server/                 # MCP Server implementation
│   └── src/mcp_idf/
│       ├── server.py           # MCP server
│       ├── client.py           # LangChain client
│       └── tools/              # MCP tools (15)
├── workspace/                  # ESP-IDF project
│   ├── main/main.c
│   └── CMakeLists.txt
├── docs/                       # Technical documentation
│   ├── ARCHITECTURE.md
│   ├── MULTI_AGENT_SYSTEM.md
│   └── OPTIMIZATION_REPORT.md
├── .devcontainer/              # VS Code Dev Container
├── docker-compose.yml
└── README.md
```

### Adding New Tools

1. **Create tool in `mcp-server/src/mcp_idf/tools/`**:
```python
class MyCustomTool:
    def execute(self, params: Dict) -> Dict:
        # Your tool logic
        return {"success": True, "data": result}
```

2. **Register in MCP server** (`mcp-server/src/mcp_idf/server.py`):
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_custom_tool":
        tool = MyCustomTool()
        return tool.execute(arguments)
```

3. **Use in agent** (`agent/orchestrator.py`):
```python
async def _custom_action(self) -> Dict[str, Any]:
    tool = self.tools["my_custom_tool"]
    result = await tool.ainvoke({"param": "value"})
    return result
```

### Running Tests

```bash
# Validate system
./verify_phase1.sh

# Full test suite
./test_multi_agent_system.sh

# Test specific component
docker compose exec mcp-server pytest tests/test_orchestrator.py
```

---

## 📚 Documentation

### Core Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and diagrams
- **[Multi-Agent System](docs/MULTI_AGENT_SYSTEM.md)** - Detailed agent roles and workflows
- **[Optimization Report](docs/OPTIMIZATION_REPORT.md)** - Performance analysis and improvements
- **[Executive Summary](docs/EXECUTIVE_SUMMARY.md)** - High-level overview for decision makers

### Additional Resources

- **[ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/)** - Official ESP32 framework docs
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - MCP specification
- **[LangChain Documentation](https://python.langchain.com/)** - Agent framework docs

### Quick Reference

```bash
# View architecture
python3 show_architecture.py

# Workflow demonstration
python3 demo_workflow_simple.py

# Check system status
./verify_phase1.sh
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/esp32-multi-agent.git
cd esp32-multi-agent
```

### 2. Create Feature Branch

```bash
git checkout -b feature/amazing-feature
```

### 3. Make Changes

- Follow existing code style
- Add tests for new features
- Update documentation

### 4. Test Your Changes

```bash
# Run test suite
./test_multi_agent_system.sh

# Verify no regressions
./verify_phase1.sh
```

### 5. Submit Pull Request

- Clear description of changes
- Link related issues
- Include before/after metrics if performance-related

### Areas for Contribution

- 🧠 **LLM Integration** - GPT-4/Claude for intelligent code fixes
- 📦 **GitHub Import** - Automated project cloning and validation
- 🌐 **Web Dashboard** - Real-time workflow visualization
- 🔌 **REST API** - Remote orchestrator control
- 📊 **Metrics Database** - Historical performance tracking

---

## 🐛 Troubleshooting

### Common Issues

**Docker containers not starting**
```bash
# Check Docker status
docker compose ps

# View logs
docker compose logs mcp-server

# Restart services
docker compose restart
```

**Serial port not accessible**
```bash
# macOS: Find correct port
ls /dev/cu.*

# Linux: Add user to dialout group
sudo usermod -a -G dialout $USER
```

**Build cache not working**
```bash
# Check cache directory
ls -la workspace/.artifacts_cache/

# Clear cache if corrupted
rm -rf workspace/.artifacts_cache/*
```

**QEMU simulation fails**
```bash
# Verify QEMU installation
docker compose exec mcp-server qemu-system-xtensa --version

# Check ESP-IDF version supports QEMU
docker compose exec mcp-server bash -lc "idf.py --version"
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Espressif Systems** - ESP-IDF framework and QEMU support
- **Anthropic** - Model Context Protocol specification
- **LangChain** - Agent orchestration framework
- **Docker Community** - Containerization platform

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/esp32-multi-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/esp32-multi-agent/discussions)
- **Email**: your.email@example.com

---

## 🗺️ Roadmap

### Phase 2 (Planned)

- [ ] **LLM Integration** - GPT-4/Claude for Developer agent (2-3 weeks)
- [ ] **GitHub Import** - Automated repo cloning and validation (1 week)
- [ ] **Web Dashboard** - React + FastAPI real-time UI (3-4 weeks)
- [ ] **REST API** - Remote workflow control (2 weeks)
- [ ] **Metrics DB** - PostgreSQL/InfluxDB for analytics (2 weeks)

### Future Enhancements

- [ ] Multi-device parallel flashing
- [ ] Unity test framework integration
- [ ] Static analysis (clang-tidy, cppcheck)
- [ ] Coverage reporting
- [ ] GitHub Actions CI/CD templates
- [ ] Firmware signing and OTA updates

---

<div align="center">

**Made with ❤️ for the ESP32 community**

[⭐ Star this repo](https://github.com/yourusername/esp32-multi-agent) • [📖 Read the docs](docs/) • [🐛 Report bug](issues) • [💡 Request feature](issues)

</div>
