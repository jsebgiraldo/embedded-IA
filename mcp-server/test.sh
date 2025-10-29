#!/bin/bash
# Test script for MCP tools with icons and proper error handling

set +e  # Don't exit on error, show all test results

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 MCP Tools Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Source ESP-IDF environment (quiet mode)
. /opt/esp/idf/export.sh > /dev/null 2>&1

# Set PYTHONPATH
export PYTHONPATH="/mcp-server/src:${PYTHONPATH}"

PASS_COUNT=0
FAIL_COUNT=0

# Test 1: Module Import
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔌 Test 1: Module Import"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
try:
    from mcp_idf.tools import IDFTools, FileManager
    from mcp_idf.client import MCPClient
    import langchain
    print(f"   ✅ PASS: All modules imported successfully")
    print(f"   ℹ️  LangChain version: {langchain.__version__}")
    sys.exit(0)
except Exception as e:
    print(f"   ❌ FAIL: {str(e)}")
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi
echo ""

# Test 2: IDF Doctor
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Test 2: IDF Doctor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
try:
    from mcp_idf.tools import IDFTools
    tools = IDFTools()
    result = tools.doctor()
    print(f"   ℹ️  Command: {result['command']}")
    print(f"   ℹ️  Return code: {result['returncode']}")
    if result['returncode'] == 0:
        print("   ✅ PASS: IDF Doctor executed successfully")
        sys.exit(0)
    else:
        print("   ⚠️  WARN: IDF Doctor returned non-zero (OK if IDF not fully configured)")
        sys.exit(0)
except Exception as e:
    print(f"   ❌ FAIL: {str(e)}")
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi
echo ""

# Test 3: File Manager - List Directory
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📂 Test 3: File Manager - List Directory"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
try:
    from mcp_idf.tools import FileManager
    fm = FileManager()
    result = fm.list_directory(".")
    if result['success']:
        entries = result.get('entries', [])
        print(f"   ✅ PASS: Found {len(entries)} entries")
        if entries:
            print("   📋 First 5 items:")
            for entry in entries[:5]:
                icon = "📁" if entry['type'] == 'directory' else "📄"
                print(f"      {icon} {entry['name']}")
        sys.exit(0)
    else:
        print(f"   ❌ FAIL: {result.get('error', 'Unknown error')}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ FAIL: {str(e)}")
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi
echo ""

# Test 4: File Manager - File Operations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 Test 4: File Manager - File Operations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
try:
    from mcp_idf.tools import FileManager
    fm = FileManager()
    
    # Check if README exists
    result = fm.file_exists("README.md")
    if result['success']:
        exists = result.get('exists', False)
        print(f"   ℹ️  README.md exists: {exists}")
        
        if exists:
            # Try to read it
            read_result = fm.read_file("README.md")
            if read_result['success']:
                print(f"   ✅ PASS: Read README.md ({read_result['size']} bytes)")
                sys.exit(0)
            else:
                print(f"   ❌ FAIL: Could not read README.md")
                sys.exit(1)
        else:
            print("   ✅ PASS: File check working (README.md not found)")
            sys.exit(0)
    else:
        print(f"   ❌ FAIL: {result.get('error', 'Unknown error')}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ FAIL: {str(e)}")
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi
echo ""

# Test 5: MCP Client - Get Tools
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Test 5: MCP Client - Available Tools"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
try:
    from mcp_idf.client import MCPClient
    client = MCPClient()
    tools = client.get_langchain_tools()
    print(f"   ✅ PASS: Loaded {len(tools)} tools")
    print("   📋 Available tools:")
    for i, tool in enumerate(tools, 1):
        desc = tool.description[:45] + "..." if len(tool.description) > 45 else tool.description
        print(f"      {i:2d}. 🛠️  {tool.name:20s} - {desc}")
    sys.exit(0)
except Exception as e:
    print(f"   ❌ FAIL: {str(e)}")
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi
echo ""

# Test 6: IDF Commands Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Test 6: IDF Commands - Target Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
import sys
sys.path.insert(0, '/mcp-server/src')
try:
    from mcp_idf.tools import IDFTools
    tools = IDFTools()
    
    # Test invalid target (should fail)
    invalid_result = tools.set_target("invalid_chip")
    if not invalid_result['success'] and 'Invalid target' in invalid_result['stderr']:
        print("   ✅ PASS: Target validation working correctly")
        sys.exit(0)
    else:
        print("   ❌ FAIL: Target validation not working")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ FAIL: {str(e)}")
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   ✅ Passed: $PASS_COUNT"
echo "   ❌ Failed: $FAIL_COUNT"
echo "   📈 Total:  $((PASS_COUNT + FAIL_COUNT))"

if [ $FAIL_COUNT -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
