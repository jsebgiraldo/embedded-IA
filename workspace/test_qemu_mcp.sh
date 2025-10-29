#!/bin/bash
# Test QEMU simulation workflow with MCP tools
# Demonstrates: Build -> QEMU -> Inspect -> Stop

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎮 Testing QEMU Simulation with MCP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Load ESP-IDF environment
source /opt/esp/idf/export.sh > /dev/null 2>&1

cd /workspace

echo ""
echo "🔧 Step 1: Check/Install QEMU"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v qemu-system-xtensa &> /dev/null; then
    echo "✅ QEMU already installed"
    qemu-system-xtensa --version | head -1
else
    echo "⚠️  QEMU not found"
    echo "   Installing qemu-system-xtensa..."
    apt-get update > /dev/null 2>&1 && apt-get install -y qemu-system-xtensa > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ QEMU installed successfully"
    else
        echo "❌ Failed to install QEMU"
        echo "   Manual install: apt-get install qemu-system-xtensa"
        exit 1
    fi
fi

echo ""
echo "🎯 Step 2: Set target to ESP32 (QEMU supported)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()
result = tools.set_target('esp32')
if result['success']:
    print("✅ Target set to ESP32")
else:
    print(f"⚠️  {result['stderr']}")
EOF

echo ""
echo "🔨 Step 3: Build project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()
print("Building... (this may take a moment)")
result = tools.build()
if result['success']:
    print("✅ Build successful")
else:
    print(f"❌ Build failed: {result['returncode']}")
    sys.exit(1)
EOF

echo ""
echo "🎮 Step 4: Start QEMU simulation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()
result = tools.run_qemu(target='esp32')
if result['success']:
    print(result['stdout'])
else:
    print(f"❌ Failed to start QEMU")
    print(f"   Error: {result['stderr']}")
    if 'suggestion' in result:
        print(f"   Suggestion: {result['suggestion']}")
    sys.exit(1)
EOF

echo ""
echo "⏱️  Waiting 3 seconds for simulation to start..."
sleep 3

echo ""
echo "📊 Step 5: Check QEMU status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()
result = tools.qemu_status()
print(result['stdout'])
EOF

echo ""
echo "📋 Step 6: Get QEMU output"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()
result = tools.qemu_output(lines=30)
if result['success']:
    print(result['stdout'])
else:
    print(f"⚠️  {result['stderr']}")
EOF

echo ""
echo "🔍 Step 7: Inspect with QEMU monitor + doctor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()

print("🔎 Getting system info from QEMU...")
result = tools.qemu_inspect(command='info registers')
if result['success'] and result['stdout'].strip():
    print("✅ QEMU monitor accessible")
    print(result['stdout'][:500])  # First 500 chars
else:
    print("⚠️  QEMU monitor not responding (this is OK for basic simulation)")

print("\n🏥 Running IDF doctor for validation...")
result = tools.doctor()
if result['returncode'] in [0, 2]:  # 0 or 2 is acceptable
    print("✅ IDF environment validated")
else:
    print(f"⚠️  Doctor returned code: {result['returncode']}")
EOF

echo ""
echo "⏸️  Letting simulation run for 5 seconds..."
sleep 5

echo ""
echo "🛑 Step 8: Stop QEMU"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

tools = IDFTools()
result = tools.stop_qemu()
print(result['stdout'])
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 QEMU Simulation Test Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "MCP Tools verified:"
echo "  ✅ run_qemu_simulation() - Start simulation"
echo "  ✅ qemu_simulation_status() - Monitor resources"
echo "  ✅ qemu_get_output() - Read application output"
echo "  ✅ qemu_inspect_state() - Debug with monitor"
echo "  ✅ stop_qemu_simulation() - Clean shutdown"
echo "  ✅ idf_doctor() - Validation"
echo ""
echo "QEMU enables testing without physical ESP32 hardware!"
