#!/bin/bash
# Quick verification script - checks all Phase 1 deliverables

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║        FASE 1 - Verificación de Entregables                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
        return 0
    else
        echo -e "${RED}❌${NC} $1 (MISSING)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $1/"
        return 0
    else
        echo -e "${RED}❌${NC} $1/ (MISSING)"
        return 1
    fi
}

total=0
passed=0

echo "📚 Documentación:"
check_file "EXECUTIVE_SUMMARY.md" && ((passed++))
((total++))
check_file "MULTI_AGENT_SYSTEM.md" && ((passed++))
((total++))
check_file "ARCHITECTURE.md" && ((passed++))
((total++))
check_file "OPTIMIZATION_REPORT.md" && ((passed++))
((total++))
check_file "README_DOCS.md" && ((passed++))
((total++))
check_file "PHASE1_COMPLETE.md" && ((passed++))
((total++))
check_file "PHASE1_SUMMARY.txt" && ((passed++))
((total++))
check_file "PHASE1_FINAL_REPORT.txt" && ((passed++))
((total++))

echo ""
echo "💻 Implementación:"
check_file "agent/orchestrator.py" && ((passed++))
((total++))
check_file "agent/demo_workflow.py" && ((passed++))
((total++))
check_file "agent/__init__.py" && ((passed++))
((total++))

echo ""
echo "🔧 MCP Server:"
check_dir "mcp-server/src/mcp_idf" && ((passed++))
((total++))
check_file "mcp-server/src/mcp_idf/client.py" && ((passed++))
((total++))
check_file "mcp-server/src/mcp_idf/tools/artifact_manager.py" && ((passed++))
((total++))
check_file "mcp-server/src/mcp_idf/tools/qemu_manager.py" && ((passed++))
((total++))

echo ""
echo "🧪 Testing & Demos:"
check_file "test_multi_agent_system.sh" && ((passed++))
((total++))
check_file "show_architecture.py" && ((passed++))
((total++))

echo ""
echo "📦 Build Cache:"
check_dir "workspace/.artifacts_cache" && ((passed++))
((total++))

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo -e "Resultado: ${GREEN}${passed}${NC}/${total} archivos verificados"

if [ $passed -eq $total ]; then
    echo -e "${GREEN}✅ FASE 1 COMPLETADA - Todos los archivos presentes${NC}"
    echo ""
    echo "🚀 Siguiente paso:"
    echo "   ./test_multi_agent_system.sh"
    exit 0
else
    echo -e "${RED}⚠️  Algunos archivos faltan${NC}"
    exit 1
fi
