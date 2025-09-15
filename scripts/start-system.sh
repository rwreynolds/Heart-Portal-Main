#!/bin/bash

# Heart Portal System Startup Script
# Starts all components in the correct order

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        error "Port $port is already in use"
        echo "Kill the process with: lsof -ti :$port | xargs kill"
        return 1
    fi
    return 0
}

# Function to start a component
start_component() {
    local name=$1
    local dir=$2
    local port=$3
    local script=$4

    log "Starting $name on port $port..."
    
    if ! check_port $port; then
        return 1
    fi
    
    cd "$dir"
    source venv/bin/activate
    
    # Start in background and capture PID
    python3 $script > /tmp/heart-portal-$name.log 2>&1 &
    local pid=$!
    echo $pid > /tmp/heart-portal-$name.pid
    
    # Give it a moment to start
    sleep 2
    
    # Check if still running
    if ps -p $pid > /dev/null; then
        success "$name started (PID: $pid) - http://localhost:$port"
    else
        error "$name failed to start - check /tmp/heart-portal-$name.log"
        return 1
    fi
    
    cd - > /dev/null
}

main() {
    echo "========================================"
    echo "🚀 Starting Heart Portal System"
    echo "========================================"
    echo
    
    # Check environment
    log "Checking development environment..."
    if ! ./scripts/dev-check.sh > /dev/null 2>&1; then
        error "Environment check failed. Run './scripts/dev-check.sh' for details"
        exit 1
    fi
    success "Environment check passed"
    echo
    
    # Start components in order
    log "Starting all components..."
    echo
    
    # Start backend services first
    start_component "Nutrition-Database" "Nutrition-Database" 5000 "app.py" || exit 1
    start_component "Food-Base" "Food-Base" 5001 "app.py" || exit 1
    start_component "Blog-Manager" "Blog-Manager" 5002 "app.py" || exit 1
    
    # Start main app last (navigation hub)
    start_component "Main-App" "main-app" 3000 "main_app.py" || exit 1
    
    echo
    success "🎉 Heart Portal System Started Successfully!"
    echo
    echo "📱 Access Points:"
    echo "  Main Portal:      http://localhost:3000"
    echo "  Nutrition-DB:     http://localhost:5000"  
    echo "  Food-Base:        http://localhost:5001"
    echo "  Blog-Manager:     http://localhost:5002"
    echo
    echo "📋 Management:"
    echo "  Stop system:      ./scripts/stop-system.sh"
    echo "  View logs:        tail -f /tmp/heart-portal-*.log"
    echo "  Check status:     ./scripts/status-system.sh"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal System Startup"
        echo
        echo "Usage: ./start-system.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  (no args)   Start all components"
        echo
        echo "This script starts all Heart Portal components:"
        echo "  - Main App (port 3000)"
        echo "  - Nutrition-Database (port 5000)"
        echo "  - Food-Base (port 5001)"
        echo "  - Blog-Manager (port 5002)"
        ;;
    *)
        main "$@"
        ;;
esac