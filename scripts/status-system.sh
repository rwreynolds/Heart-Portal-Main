#!/bin/bash

# Heart Portal System Status Script
# Shows the status of all components

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_component() {
    local name=$1
    local port=$2
    local pidfile="/tmp/heart-portal-$name.pid"
    
    printf "%-18s " "$name:"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            # Check if port is responding
            if curl -s "http://localhost:$port" > /dev/null 2>&1; then
                success "Running (PID: $pid) - http://localhost:$port"
            else
                warning "Process running but not responding on port $port"
            fi
        else
            error "PID file exists but process not running"
        fi
    else
        # Check if something is running on the port
        if lsof -i :$port > /dev/null 2>&1; then
            warning "Something running on port $port (unknown process)"
        else
            error "Not running"
        fi
    fi
}

main() {
    echo "========================================"
    echo "📊 Heart Portal System Status"
    echo "========================================"
    echo
    
    check_component "Main-App" 3000
    check_component "Nutrition-Database" 5000
    check_component "Food-Base" 5001  
    check_component "Blog-Manager" 5002
    
    echo
    echo "📋 Quick Commands:"
    echo "  Start system:     ./scripts/start-system.sh"
    echo "  Stop system:      ./scripts/stop-system.sh"
    echo "  View logs:        tail -f /tmp/heart-portal-*.log"
    echo "  Main Portal:      http://localhost:3000"
}

main "$@"