#!/bin/bash

# Script para gestionar Ollama en Docker
# Uso: ./scripts/ollama-docker.sh [start|stop|status|pull|run|logs]

set -e

CONTAINER_NAME="esp32-ollama"
MODEL_NAME="${LLM_MODEL:-qwen2.5-coder:14b}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Ollama Docker Manager - ESP32 DevAgent             ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Verificar si el contenedor existe
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Verificar si el contenedor está corriendo
container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Iniciar servicios
start_ollama() {
    print_header
    echo -e "${YELLOW}🚀 Iniciando Ollama en Docker...${NC}"
    
    # Iniciar compose (solo ollama)
    docker-compose up -d ollama
    
    echo -e "${GREEN}✅ Esperando a que Ollama esté listo...${NC}"
    sleep 5
    
    # Verificar health
    for i in {1..30}; do
        if docker exec $CONTAINER_NAME ollama list > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Ollama está listo!${NC}"
            show_status
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "${RED}❌ Timeout esperando a Ollama${NC}"
    return 1
}

# Detener Ollama
stop_ollama() {
    print_header
    echo -e "${YELLOW}🛑 Deteniendo Ollama...${NC}"
    
    if container_running; then
        docker-compose stop ollama
        echo -e "${GREEN}✅ Ollama detenido${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama no estaba corriendo${NC}"
    fi
}

# Mostrar estado
show_status() {
    print_header
    
    if container_running; then
        echo -e "${GREEN}✅ Estado: CORRIENDO${NC}"
        echo ""
        
        # Stats del contenedor
        echo -e "${BLUE}📊 Recursos:${NC}"
        docker stats --no-stream --format "  CPU: {{.CPUPerc}}\n  RAM: {{.MemUsage}}" $CONTAINER_NAME
        echo ""
        
        # Modelos disponibles
        echo -e "${BLUE}🤖 Modelos disponibles:${NC}"
        docker exec $CONTAINER_NAME ollama list 2>/dev/null || echo "  (ninguno instalado)"
        echo ""
        
        # Endpoint
        echo -e "${BLUE}🌐 Endpoint:${NC}"
        echo "  http://localhost:11434"
        echo ""
    else
        echo -e "${RED}❌ Estado: DETENIDO${NC}"
        echo ""
        echo "Usa: $0 start"
    fi
}

# Descargar modelo
pull_model() {
    print_header
    
    if ! container_running; then
        echo -e "${RED}❌ Ollama no está corriendo${NC}"
        echo "Usa: $0 start"
        exit 1
    fi
    
    MODEL="${1:-$MODEL_NAME}"
    
    echo -e "${YELLOW}📥 Descargando modelo: ${MODEL}${NC}"
    echo ""
    
    docker exec -it $CONTAINER_NAME ollama pull "$MODEL"
    
    echo ""
    echo -e "${GREEN}✅ Modelo descargado!${NC}"
}

# Ejecutar modelo interactivo
run_model() {
    print_header
    
    if ! container_running; then
        echo -e "${RED}❌ Ollama no está corriendo${NC}"
        echo "Usa: $0 start"
        exit 1
    fi
    
    MODEL="${1:-$MODEL_NAME}"
    
    echo -e "${YELLOW}💬 Iniciando chat con: ${MODEL}${NC}"
    echo -e "${BLUE}   (Ctrl+D para salir)${NC}"
    echo ""
    
    docker exec -it $CONTAINER_NAME ollama run "$MODEL"
}

# Ver logs
show_logs() {
    print_header
    echo -e "${BLUE}📋 Logs de Ollama:${NC}"
    echo ""
    docker logs --tail 50 -f $CONTAINER_NAME
}

# Test rápido
test_ollama() {
    print_header
    
    if ! container_running; then
        echo -e "${RED}❌ Ollama no está corriendo${NC}"
        exit 1
    fi
    
    MODEL="${1:-$MODEL_NAME}"
    
    echo -e "${YELLOW}🧪 Test rápido con ${MODEL}${NC}"
    echo ""
    
    # Test simple
    PROMPT="Write a hello world in C for ESP32"
    
    echo -e "${BLUE}Prompt:${NC} $PROMPT"
    echo ""
    echo -e "${BLUE}Respuesta:${NC}"
    
    docker exec $CONTAINER_NAME curl -s http://localhost:11434/api/generate -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"$PROMPT\",
        \"stream\": false
    }" | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])"
    
    echo ""
    echo -e "${GREEN}✅ Test completado${NC}"
}

# Reiniciar
restart_ollama() {
    stop_ollama
    sleep 2
    start_ollama
}

# Menú principal
case "${1:-}" in
    start)
        start_ollama
        ;;
    stop)
        stop_ollama
        ;;
    restart)
        restart_ollama
        ;;
    status)
        show_status
        ;;
    pull)
        pull_model "${2:-}"
        ;;
    run)
        run_model "${2:-}"
        ;;
    logs)
        show_logs
        ;;
    test)
        test_ollama "${2:-}"
        ;;
    *)
        print_header
        echo "Uso: $0 {start|stop|restart|status|pull|run|logs|test} [modelo]"
        echo ""
        echo "Comandos:"
        echo "  start              Iniciar Ollama"
        echo "  stop               Detener Ollama"
        echo "  restart            Reiniciar Ollama"
        echo "  status             Ver estado y recursos"
        echo "  pull [modelo]      Descargar modelo"
        echo "  run [modelo]       Chat interactivo"
        echo "  logs               Ver logs en tiempo real"
        echo "  test [modelo]      Test rápido"
        echo ""
        echo "Ejemplos:"
        echo "  $0 start"
        echo "  $0 pull qwen2.5-coder:14b"
        echo "  $0 run qwen2.5-coder:14b"
        echo "  $0 test"
        echo "  $0 status"
        echo ""
        exit 1
        ;;
esac
