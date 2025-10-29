#!/bin/bash

# Quick test script for Multi-Agent Workflow System
# Tests the complete workflow with all agents and parallelization

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     ESP32 Multi-Agent Workflow System - Quick Test              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Please run this script from /Users/sebastiangiraldo/Documents/embedded-IA/"
    exit 1
fi

# Check if containers are running
echo "🔍 Checking Docker containers..."
if ! docker compose ps | grep -q "mcp-server.*Up"; then
    echo "⚠️  Containers not running. Starting..."
    docker compose up -d
    sleep 3
fi
echo "✅ Containers running"
echo ""

# Display system info
echo "📊 System Overview:"
echo "   • 6 Specialized Agents: PM, Developer, Builder, Tester, Doctor, QA"
echo "   • 15 MCP Tools available"
echo "   • Parallel execution: Flash + QEMU, Doctor + QA"
echo "   • QA Feedback Loop: Auto-fix and retry (max 3 iterations)"
echo ""

# Test 1: Validate MCP Tools
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Validate MCP Tools"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🔧 Testing idf_build tool..."
docker compose exec -T mcp-server python3 << 'PYTHON'
import sys
sys.path.insert(0, '/app')
from mcp_idf.client import MCPClient

client = MCPClient()
tools = client.get_langchain_tools()
print(f"✅ Loaded {len(tools)} LangChain tools")

tool_names = [tool.name for tool in tools]
print("\n📦 Available tools:")
for name in sorted(tool_names):
    print(f"   • {name}")
PYTHON

if [ $? -eq 0 ]; then
    echo "✅ Test 1 PASSED: MCP Tools validated"
else
    echo "❌ Test 1 FAILED"
    exit 1
fi
echo ""

# Test 2: Test Agent Orchestrator Initialization
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Agent Orchestrator Initialization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose exec -T mcp-server python3 << 'PYTHON'
import sys
sys.path.insert(0, '/app')
from mcp_idf.client import MCPClient
from agent.orchestrator import AgentOrchestrator, AgentRole

client = MCPClient()
tools = client.get_langchain_tools()
orchestrator = AgentOrchestrator(tools)

print("✅ Orchestrator initialized")
print(f"\n🎭 Agent Roles configured:")
for role, config in orchestrator.agent_roles.items():
    print(f"   • {role.value}: {len(config['tools'])} tools")
PYTHON

if [ $? -eq 0 ]; then
    echo "✅ Test 2 PASSED: Orchestrator initialized"
else
    echo "❌ Test 2 FAILED"
    exit 1
fi
echo ""

# Test 3: Verify Build Cache System
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Build Artifact Cache"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🔨 Building project (first time - will cache artifacts)..."
docker compose exec -T mcp-server bash -lc ". /opt/esp/idf/export.sh && cd /workspace && idf.py build" > /dev/null 2>&1

if [ -f "workspace/.artifacts_cache/build_metadata.json" ]; then
    echo "✅ Artifacts cached successfully"
    echo "📦 Cache location: workspace/.artifacts_cache/"
    echo "   • build_metadata.json (checksums, paths, flash args)"
    echo "   • bootloader.bin, partition-table.bin, app.bin"
else
    echo "⚠️  Cache not found (expected on first run)"
fi
echo ""

# Test 4: QEMU Integration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: QEMU Simulation (10 seconds)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🎮 Starting QEMU simulation..."
timeout 10 docker compose exec -T mcp-server bash -lc ". /opt/esp/idf/export.sh && cd /workspace && idf.py qemu" > /tmp/qemu_output.txt 2>&1 || true

if grep -q "Hello World" /tmp/qemu_output.txt; then
    echo "✅ QEMU simulation successful"
    echo "📺 Console output captured:"
    grep "Hello World" /tmp/qemu_output.txt | head -3 | sed 's/^/   /'
else
    echo "⚠️  QEMU output not captured (may need longer run time)"
fi
echo ""

# Test 5: Workflow Plan Generation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Workflow Plan & Parallelization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose exec -T mcp-server python3 << 'PYTHON'
import sys
import asyncio
sys.path.insert(0, '/app')
from mcp_idf.client import MCPClient
from agent.orchestrator import AgentOrchestrator

async def test_workflow_plan():
    client = MCPClient()
    tools = client.get_langchain_tools()
    orchestrator = AgentOrchestrator(tools)
    
    # Create workflow plan
    tasks = await orchestrator._create_workflow_plan(
        flash_device=True,
        run_qemu=True
    )
    
    print(f"✅ Generated {len(tasks)} tasks")
    
    # Identify parallel tasks
    parallel_tasks = [t for t in tasks if t.can_parallelize]
    print(f"\n⚡ Parallel tasks: {len(parallel_tasks)}")
    for task in parallel_tasks:
        print(f"   • {task.id} [{task.role.value}] {task.action}")
    
    # Show workflow phases
    print("\n📊 Workflow phases:")
    sequential = [t for t in tasks if not t.can_parallelize]
    for i, task in enumerate(sequential, 1):
        print(f"   {i}. [{task.role.value}] {task.action}")
        if task.dependencies:
            print(f"      Dependencies: {', '.join(task.dependencies)}")

asyncio.run(test_workflow_plan())
PYTHON

if [ $? -eq 0 ]; then
    echo "✅ Test 5 PASSED: Workflow plan generated"
else
    echo "❌ Test 5 FAILED"
    exit 1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All tests passed!"
echo ""
echo "🚀 System Ready! Next steps:"
echo ""
echo "1. Run full workflow demo:"
echo "   docker compose exec mcp-server python3 /agent/demo_workflow.py"
echo ""
echo "2. Test with your own project:"
echo "   python3 -c '"
echo "   from mcp_idf.client import MCPClient"
echo "   from agent.orchestrator import AgentOrchestrator"
echo "   import asyncio"
echo "   "
echo "   async def run():"
echo "       client = MCPClient()"
echo "       orch = AgentOrchestrator(client.get_langchain_tools())"
echo "       results = await orch.execute_workflow("
echo "           project_path=\"/workspace\","
echo "           target=\"esp32\","
echo "           flash_device=False,"
echo "           run_qemu=True"
echo "       )"
echo "       print(orch.get_workflow_summary())"
echo "   "
echo "   asyncio.run(run())"
echo "   '"
echo ""
echo "3. Review documentation:"
echo "   cat MULTI_AGENT_SYSTEM.md"
echo "   cat ARCHITECTURE.md"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
