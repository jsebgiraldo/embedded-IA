# Workspace - ESP-IDF Project Template

This directory serves as the **default workspace** for the multi-agent system to build, test, and deploy ESP32 firmware.

## 📁 Structure

```
workspace/
├── main/                  # Main application code
│   ├── main.c            # Entry point (app_main)
│   └── CMakeLists.txt    # Component build config
├── CMakeLists.txt        # Project configuration
├── sdkconfig            # ESP-IDF configuration (auto-generated)
└── .artifacts_cache/    # Build cache (auto-created)
```

## 🎯 Purpose

- **Template Project**: Clean ESP-IDF project ready for customization
- **Agent Workspace**: Default target for multi-agent orchestrator operations
- **Build Cache**: Stores artifacts for 83% faster rebuilds

## 🚀 Usage

### Option 1: Use Template Project

```bash
# Build the included Hello World example
docker compose exec mcp-server bash -lc "cd /workspace && idf.py build"

# Flash to device
docker compose exec mcp-server bash -lc "cd /workspace && idf.py -p /dev/ttyUSB0 flash"

# Run in QEMU
docker compose exec mcp-server bash -lc "cd /workspace && idf.py qemu"
```

### Option 2: Import Your Project

Replace the contents with your own ESP-IDF project:

```bash
# Backup template
mv workspace workspace-template

# Clone your project
git clone https://github.com/youruser/your-esp32-project.git workspace

# Or copy existing project
cp -r /path/to/your/project workspace/
```

### Option 3: Create New Project

```bash
docker compose exec mcp-server bash -lc "cd /workspace && idf.py create-project my-project"
```

## 🔧 Multi-Agent System Integration

The orchestrator automatically:
- ✅ Detects project in `/workspace` mount point
- ✅ Creates `.artifacts_cache/` for intelligent caching
- ✅ Runs builds, tests, and QEMU simulations here
- ✅ Stores build metadata with SHA256 checksums

## 📦 Artifacts Cache

The `.artifacts_cache/` directory stores:
- **build_metadata.json**: Source file checksums and build info
- **Compiled binaries**: Cached build outputs
- **Dependencies**: Extracted from build logs

**Performance**: 3 min → 30 sec flash operations when cache hits!

## 🔄 Switching Projects

```bash
# Option A: Use Docker Compose volume override
# In docker-compose.override.yml:
services:
  mcp-server:
    volumes:
      - /path/to/your/project:/workspace

# Option B: Replace workspace directory
rm -rf workspace/*
cp -r /your/project/* workspace/

# Option C: Use symlink
rm -rf workspace
ln -s /path/to/your/project workspace
```

## 🧪 Testing

Run the example project:

```bash
# From repository root
./scripts/test_flash_cached.sh

# Or using multi-agent system
python3 examples/demo_workflow_simple.py
```

## 📝 Notes

- **Mount Point**: Docker containers mount this as `/workspace`
- **ESP-IDF Target**: Configured in `.env` (default: `esp32c6`)
- **Build Directory**: `build/` is auto-generated (ignored by git)
- **SDK Config**: `sdkconfig` is project-specific configuration

## 🔍 Current Template

The included template is a **Hello World** application that:
- Prints system information on boot
- Logs messages every second
- Demonstrates FreeRTOS task usage
- Works with both hardware and QEMU

Customize `main/main.c` to build your application!
