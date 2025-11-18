# 🤖 ESP32 Multi-Agent Development System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ESP-IDF](https://img.shields.io/badge/ESP--IDF-v6.1-blue.svg)](https://github.com/espressif/esp-idf)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> **AI-powered multi-agent orchestration system for ESP32 firmware development with intelligent caching, parallel execution, and automated QA feedback loops.**

Transform your ESP32 development workflow with specialized AI agents that coordinate build, test, and validation tasks—achieving up to 83% faster deployment cycles through smart artifact caching and parallel execution.

---

## 🌟 Key Features

### 🌐 **Real-Time Web Dashboard**
- **Live Monitoring** - Real-time agent status, logs, and metrics
- **WebSocket Updates** - Instant event notifications
- **Job Management** - Track workflows, builds, and tests
- **LLM Integration** - AI-powered chat, code generation, and bug fixing
- **Project Management** - Import and manage GitHub repositories
- **REST API** - Complete API for integration
- **SQLite Backend** - Persistent storage with full history

### 📦 **GitHub Import & CI/CD** (NEW!)
- **Automatic Import** - Clone repositories from GitHub automatically
- **Webhook Integration** - Receive push/PR events in real-time
- **Build Triggers** - Automatic builds on code changes
- **Git Operations** - Pull updates, checkout commits, track history
- **Build History** - Full audit trail with metrics and analytics
- **HMAC Validation** - Secure webhook signature verification

### 🎭 **6 Specialized Agents**
- **🎯 Project Manager** - Project setup, validation, and coordination
- **👨‍💻 Developer** - Code writing and automated bug fixing with LLM
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
- [LLM Integration](#-llm-integration)
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
- **Ollama with qwen2.5-coder:7b** (dockerized, included)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/esp32-multi-agent.git
cd esp32-multi-agent

# Copy environment template
cp .env.example .env

# Edit .env with your settings (ESP32 target, serial port, etc.)
nano .env
```

### 2. Start Services with Dashboard

```bash
# Start all services (including Web Dashboard + Ollama)
./docker-manager.sh start

# Or using docker-compose directly
docker-compose up -d

# Verify services are running
./docker-manager.sh status
```

### 3. Access the Dashboard

Open your browser at **http://localhost:8000** to see:
- Real-time agent status
- Live log streaming
- Workflow progress
- Job history and metrics

### 4. Run Your First Workflow

```bash
# Simple workflow demonstration (watch it in the dashboard!)
python3 examples/demo_dashboard_workflow.py

# Visual architecture viewer
python3 examples/show_architecture.py
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

## 🤖 LLM Integration

The system includes a local LLM (Qwen2.5-Coder) for intelligent code generation and bug fixing.

### Quick LLM Chat

```bash
# Ask a question
./scripts/chat-llm.sh "How do I use I2C on ESP32?"

# Interactive mode
./scripts/chat-llm.sh
```

### Automatic Code Fixing

The **Developer Agent** uses the LLM to automatically fix compilation errors:

```python
# The orchestrator automatically fixes bugs detected by QA
result = await orchestrator.run_workflow()

# Example fix:
# Input:  "implicit declaration of function 'gpio_set_direction'"
# Output: Added #include "driver/gpio.h"
# Confidence: high
```

### LLM Features

- **🔧 Code Generation** - Write ESP32 code from natural language
- **🐛 Bug Fixing** - Automatically fix compilation errors
- **📚 Documentation** - Explain existing code
- **💡 Best Practices** - Suggest optimizations and security improvements
- **🎯 ESP32-Specific** - Trained on embedded systems and ESP-IDF

**[Full LLM documentation →](docs/LLM_USAGE.md)**

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   User / LLM Interface                       │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌─────────────────────┐         ┌────────────────────┐
│  Web Dashboard      │         │  CLI Interface     │
│  (FastAPI+WS)       │         │  (Direct Access)   │
│  • Real-time UI     │         │  • Scripts         │
│  • REST API         │         │  • Workflows       │
│  • SQLite DB        │         │                    │
└──────────┬──────────┘         └─────────┬──────────┘
           │                              │
           └──────────┬───────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│              Agent Orchestrator (AsyncIO)                    │
│  • Task Dependency Management                                │
│  • Parallel Execution Engine                                 │
│  • QA Feedback Loop Controller                               │
│  • Event Emitter (Real-time updates)                         │
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
./scripts/test_flash_cached.sh

# Second build (with cache) - should be ~2-3 min faster
./scripts/test_flash_cached.sh
```

---

## 🌐 Web Dashboard

The ESP32 Multi-Agent System includes a **real-time web dashboard** for monitoring and managing agents, workflows, and builds.

### Features

- **📊 Real-time Monitoring**: Live agent status, logs, and metrics
- **🔌 WebSocket Events**: Instant updates without polling
- **📝 Job History**: Track all workflows, builds, and tests
- **🔍 Advanced Filtering**: Search logs by level, agent, time range
- **📈 Metrics Dashboard**: Success rates, durations, error analysis
- **🎯 REST API**: Full programmatic access

### Quick Start

```bash
# Start dashboard (included in docker-compose)
./docker-manager.sh start

# Or start standalone
cd web-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost:8000 | Main web interface |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| WebSocket | ws://localhost:8000/ws | Real-time event stream |

### REST API Examples

```bash
# Get all agents
curl http://localhost:8000/api/agents

# Get recent jobs
curl http://localhost:8000/api/jobs?limit=10

# Get logs from last hour
curl http://localhost:8000/api/logs?since_minutes=60

# Get metrics summary
curl http://localhost:8000/api/metrics/summary?since_hours=24
```

### WebSocket Integration

```javascript
// Connect to real-time events
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
  
  // Handle different event types
  if (data.type === 'agent_status_changed') {
    updateAgentUI(data.payload);
  } else if (data.type === 'log') {
    appendLog(data.payload);
  }
};
```

### Python Integration

```python
from web-server.api_client import DashboardClient

# Create client
client = DashboardClient("http://localhost:8000")

# Track workflow in dashboard
job_id = client.create_job(
    job_type="build",
    agent_id="build",
    status="running"
)

# Emit progress
client.emit_log(
    level="INFO",
    message="Building project...",
    agent_id="build",
    job_id=job_id
)

# Complete job
client.update_job(job_id, status="completed")
```

For more details, see [DOCKER_GUIDE.md](./DOCKER_GUIDE.md).

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
├── examples/                   # Demo scripts
│   ├── demo_workflow_simple.py
│   └── show_architecture.py
├── scripts/                    # Test & utility scripts
│   ├── test_flash_cached.sh
│   ├── test_multi_agent_system.sh
│   └── verify_phase1.sh
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
./scripts/verify_phase1.sh

# Full test suite
./scripts/test_multi_agent_system.sh

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
python3 examples/show_architecture.py

# Workflow demonstration
python3 examples/demo_workflow_simple.py

# Check system status
./scripts/verify_phase1.sh
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
./scripts/test_multi_agent_system.sh

# Verify no regressions
./scripts/verify_phase1.sh
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
- **Email**: jsgiraldod@hotmail.com

---

## 🗺️ Roadmap

### Phase 2 (In Development) 🚀

- [x] **LLM Integration** - Local models via Ollama + cloud APIs ⭐ NEW!
- [ ] **GitHub Import** - Automated repo cloning and validation (1 week)
- [ ] **Web Dashboard** - React + FastAPI real-time UI (3-4 weeks)
- [ ] **REST API** - Remote workflow control (2 weeks)
- [ ] **Metrics DB** - PostgreSQL/InfluxDB for analytics (2 weeks)

#### 🧠 Local LLM Support (NEW!)

Run powerful AI models locally without cloud dependencies:

```bash
# Quick setup (macOS/Linux)
./scripts/setup_local_llm.sh

# Run Ollama inside Docker (ships with qwen3-coder by default)
./scripts/ollama-docker.sh start          # start esp32-ollama service
./scripts/ollama-docker.sh status         # verify health / list models

# Choose your model tier
./scripts/setup_local_llm.sh best         # DeepSeek 16B (20GB RAM)
./scripts/setup_local_llm.sh balanced     # Qwen2.5 14B (18GB RAM) ⭐
./scripts/setup_local_llm.sh lightweight  # CodeLlama 7B (8GB RAM)
```

**Supported Models**:
- 🔥 **DeepSeek-Coder-V2 16B** - Best quality for complex debugging
- ⭐ **Qwen2.5-Coder 14B** - Excellent for ESP32/embedded (recommended)
- ⚡ **CodeLlama 13B** - Fast and efficient
- 🪶 **CodeLlama 7B** - Lightweight, works on 8GB RAM

**Need cloud performance?** Set `LLM_PROVIDER=deepseek` + `DEEPSEEK_API_KEY=...` in `.env` for instant fallback to the hosted DeepSeek endpoint. The orchestrator will keep using the local model whenever it’s available and automatically switch to DeepSeek if the container is down or the fix requires larger context.

**Test It**:
```bash
# Test LLM integration
python3 agent/llm_provider.py

# Test Developer Agent with real code fixing
python3 examples/test_developer_agent.py
```

**Documentation**: [Local LLM Setup Guide](docs/LOCAL_LLM_SETUP.md)

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

[⭐ Star this repo](https://github.com/jsebgiraldo/embedded-IA) • [📖 Read the docs](docs/) • [🐛 Report bug](https://github.com/jsebgiraldo/embedded-IA/issues) • [💡 Request feature](https://github.com/jsebgiraldo/embedded-IA/issues)

</div>
