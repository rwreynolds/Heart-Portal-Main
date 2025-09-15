#!/bin/bash

# Heart Portal System Stop Script
# Gracefully stops all components

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

stop_component() {
    local name=$1
    local pidfile="/tmp/heart-portal-$name.pid"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            log "Stopping $name (PID: $pid)..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                log "Force stopping $name..."
                kill -9 $pid
            fi
            success "$name stopped"
        else
            log "$name was not running"
        fi
        rm -f "$pidfile"
    else
        log "No PID file found for $name"
    fi
}

main() {
    echo "========================================"
    echo "🛑 Stopping Heart Portal System"
    echo "========================================"
    echo
    
    # Stop all components
    stop_component "Main-App"
    stop_component "Blog-Manager" 
    stop_component "Food-Base"
    stop_component "Nutrition-Database"
    
    # Clean up log files
    log "Cleaning up log files..."
    rm -f /tmp/heart-portal-*.log
    
    echo
    success "🎉 Heart Portal System Stopped"
}

main "$@"