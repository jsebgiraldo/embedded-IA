#!/bin/bash
# ESP32 LLM Chat Helper
# Wrapper para interactuar fácilmente con el LLM desde el host

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           🤖 ESP32 LLM Assistant                             ║${NC}"
echo -e "${BLUE}║           Powered by Qwen2.5-Coder (Ollama)                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que Ollama esté corriendo
if ! docker ps | grep -q esp32-ollama; then
    echo -e "${RED}❌ Error: Ollama container is not running${NC}"
    echo "Start it with: docker-compose up -d ollama"
    exit 1
fi

# Cargar variables de entorno
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Modo interactivo vs pregunta directa
if [ $# -eq 0 ]; then
    # Modo interactivo
    echo -e "${GREEN}🎯 Interactive Mode${NC}"
    echo "Type your questions about ESP32 development"
    echo "Commands: /help, /exit, /model, /clear"
    echo ""
    
    docker exec -it esp32-ollama ollama run ${LLM_MODEL:-qwen2.5-coder:7b}
    
else
    # Pregunta directa
    QUESTION="$*"
    
    echo -e "${YELLOW}📝 Question:${NC} $QUESTION"
    echo ""
    echo -e "${GREEN}🤖 Answer:${NC}"
    echo ""
    
    docker exec esp32-ollama ollama run ${LLM_MODEL:-qwen2.5-coder:7b} "$QUESTION" 2>/dev/null
    
    echo ""
fi
