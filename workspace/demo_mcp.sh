#!/bin/bash
# Demo script to test MCP tools with Hello World program

echo "🚀 ESP32 Hello World - MCP Tools Demo"
echo "======================================"
echo ""

# Source ESP-IDF environment
. /opt/esp/idf/export.sh > /dev/null 2>&1
export PYTHONPATH="/mcp-server/src:${PYTHONPATH}"

# Test 1: IDF Doctor
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Step 1: Running IDF Doctor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools
tools = IDFTools()
result = tools.doctor()
print(f"Return code: {result['returncode']}")
if result['returncode'] != 0:
    print("⚠️  Note: Some checks failed, but this is OK for our demo")
print("")
EOF

# Test 2: Set Target
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Step 2: Setting Target to ESP32"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools
tools = IDFTools()
result = tools.set_target("esp32")
if result['success']:
    print("✅ Target set successfully!")
else:
    print(f"Status: {result['returncode']}")
print("")
EOF

# Test 3: Build
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔨 Step 3: Building Hello World"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools
tools = IDFTools()
print("Building project... (this may take a few minutes)")
result = tools.build()
if result['returncode'] == 0:
    print("✅ Build succeeded!")
else:
    print(f"❌ Build failed with code: {result['returncode']}")
    print("\nLast 30 lines of output:")
    lines = result['stderr'].split('\n')
    for line in lines[-30:]:
        print(line)
print("")
EOF

# Test 4: Size
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Step 4: Checking Binary Size"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools
tools = IDFTools()
result = tools.size()
if result['returncode'] == 0:
    print(result['stdout'])
else:
    print("⚠️  Could not get size info (build may have failed)")
print("")
EOF

# Test 5: List files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📂 Step 5: Listing Build Artifacts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import FileManager
fm = FileManager()
result = fm.list_directory("build")
if result['success']:
    entries = result.get('entries', [])
    print(f"Found {len(entries)} items in build directory")
    print("\nKey files:")
    for entry in entries:
        if entry['name'].endswith('.bin') or entry['name'].endswith('.elf'):
            print(f"  📄 {entry['name']}")
else:
    print("⚠️  Build directory not found (build may have failed)")
print("")
EOF

# Test 6: Flash instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ Step 6: Flash Instructions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To flash the firmware to your ESP32:"
echo ""
echo "  1. Connect your ESP32 via USB"
echo "  2. Find the serial port:"
echo "     - Linux:   /dev/ttyUSB0 or /dev/ttyACM0"
echo "     - macOS:   /dev/cu.usbserial-*"
echo "     - Windows: COM3, COM4, etc."
echo ""
echo "  3. Flash using MCP:"
python3 << 'EOF'
print("     docker compose exec dev python3 << 'PYEOF'")
print("import sys")
print("sys.path.insert(0, '/mcp-server/src')")
print("from mcp_idf.tools import IDFTools")
print("tools = IDFTools()")
print("result = tools.flash(port='/dev/ttyUSB0')  # Adjust port")
print("print(result)")
print("PYEOF")
EOF
echo ""
echo "  4. Or use idf.py directly:"
echo "     idf.py -p /dev/ttyUSB0 flash monitor"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ MCP Tools Demo Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
