#!/bin/bash

# Script para gestionar el stack de ESP32 Developer Agent con Dashboard

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funciones de ayuda
print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}     ESP32 Developer Agent - Docker Management              ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para mostrar el estado
show_status() {
    print_header
    echo ""
    print_info "Estado de los contenedores:"
    docker-compose ps
    echo ""
    print_info "Acceso a servicios:"
    echo "  🌐 Dashboard:    http://localhost:8000"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo "  📡 WebSocket:    ws://localhost:8000/ws"
    echo "  🤖 Ollama/Model: http://localhost:11434 (Docker Desktop Models)"
}

# Función para iniciar servicios
start_services() {
    print_header
    print_info "Iniciando servicios..."
    docker-compose up -d
    echo ""
    print_success "Servicios iniciados correctamente"
    echo ""
    show_status
}

# Función para detener servicios
stop_services() {
    print_info "Deteniendo servicios..."
    docker-compose down
    print_success "Servicios detenidos"
}

# Función para rebuild
rebuild_services() {
    print_info "Reconstruyendo servicios..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    print_success "Servicios reconstruidos e iniciados"
    echo ""
    show_status
}

# Función para ver logs
show_logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        print_info "Mostrando logs de todos los servicios (Ctrl+C para salir)"
        docker-compose logs -f
    else
        print_info "Mostrando logs de $SERVICE (Ctrl+C para salir)"
        docker-compose logs -f "$SERVICE"
    fi
}

# Función para limpiar todo
clean_all() {
    print_warning "⚠️  ADVERTENCIA: Esto eliminará todos los contenedores, volúmenes y datos"
    read -p "¿Estás seguro? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Limpiando todo..."
        docker-compose down -v
        docker system prune -f
        print_success "Limpieza completada"
    else
        print_info "Operación cancelada"
    fi
}

# Función para entrar en un contenedor
enter_container() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        print_error "Debes especificar el servicio: dev, mcp-server o web-dashboard"
        exit 1
    fi
    print_info "Entrando en contenedor $SERVICE..."
    docker-compose exec "$SERVICE" bash
}

# Función para backup de la base de datos
backup_database() {
    print_info "Realizando backup de la base de datos..."
    BACKUP_FILE="dashboard-backup-$(date +%Y%m%d-%H%M%S).db"
    docker-compose exec web-dashboard cp /app/data/agent_dashboard.db "/app/data/$BACKUP_FILE"
    print_success "Backup creado: $BACKUP_FILE"
}

# Menu principal
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    rebuild)
        rebuild_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    exec)
        enter_container "$2"
        ;;
    backup)
        backup_database
        ;;
    clean)
        clean_all
        ;;
    help|*)
        print_header
        echo ""
        echo "Uso: $0 [comando] [opciones]"
        echo ""
        echo "Comandos disponibles:"
        echo "  start              - Iniciar todos los servicios"
        echo "  stop               - Detener todos los servicios"
        echo "  restart            - Reiniciar todos los servicios"
        echo "  rebuild            - Reconstruir e iniciar servicios"
        echo "  status             - Mostrar estado de servicios"
        echo "  logs [servicio]    - Ver logs (todos o de un servicio específico)"
        echo "  exec <servicio>    - Entrar en un contenedor (dev, mcp-server, web-dashboard)"
        echo "  backup             - Hacer backup de la base de datos"
        echo "  clean              - Limpiar todo (contenedores y volúmenes)"
        echo "  help               - Mostrar esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  $0 start"
        echo "  $0 logs web-dashboard"
        echo "  $0 exec dev"
        echo ""
        ;;
esac
