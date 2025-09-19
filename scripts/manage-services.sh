#!/bin/bash

# Heart Portal Service Management Script
# Consolidates start-system.sh, stop-system.sh, status-system.sh, update-main-service.sh
# Usage: ./manage-services.sh {start|stop|status|restart|update} [service-name]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_HOST="129.212.181.161"
SERVER_USER="heartportal"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"

# Service definitions
SERVICES=(
    "heart-portal-main:3000"
    "heart-portal-nutrition:5000"
    "heart-portal-food:5001"
    "heart-portal-blog:5002"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect if we're running locally or on the server
if [ "$(whoami)" = "$SERVER_USER" ] && [ "$(hostname -I 2>/dev/null | grep -q "$SERVER_HOST" && echo "server" || echo "local")" = "server" ]; then
    RUN_MODE="server"
    SSH_CMD=""
else
    RUN_MODE="local"
    SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"
fi

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

execute_command() {
    local cmd="$1"
    if [ "$RUN_MODE" = "local" ]; then
        $SSH_CMD "$cmd"
    else
        eval "$cmd"
    fi
}

show_usage() {
    echo "Usage: $0 {start|stop|status|restart|update} [service-name]"
    echo
    echo "Commands:"
    echo "  start    - Start all services or specified service"
    echo "  stop     - Stop all services or specified service"
    echo "  status   - Show status of all services or specified service"
    echo "  restart  - Restart all services or specified service"
    echo "  update   - Update and restart main service"
    echo
    echo "Services:"
    for service_def in "${SERVICES[@]}"; do
        service_name="${service_def%%:*}"
        port="${service_def##*:}"
        echo "  ${service_name##*-} (${service_name}:${port})"
    done
    echo
    echo "Examples:"
    echo "  $0 status                    # Show all service status"
    echo "  $0 restart main              # Restart main service only"
    echo "  $0 start heart-portal-blog   # Start blog service"
    echo "  $0 update                    # Update main service"
}

get_service_status() {
    local service_name="$1"
    local status

    if execute_command "systemctl is-active $service_name" >/dev/null 2>&1; then
        status="active"
    else
        status="inactive"
    fi

    echo "$status"
}

show_service_status() {
    local service_name="$1"
    local port="$2"
    local status=$(get_service_status "$service_name")

    if [ "$status" = "active" ]; then
        success "✓ $service_name (port $port) - Running"
        # Test port connectivity
        if execute_command "nc -z localhost $port" >/dev/null 2>&1; then
            echo "  Port $port: Responding"
        else
            warning "  Port $port: Not responding"
        fi
    else
        error "✗ $service_name (port $port) - Stopped"
    fi
}

start_service() {
    local service_name="$1"
    log "Starting $service_name..."

    if execute_command "sudo systemctl start $service_name"; then
        success "Started $service_name"
        sleep 2
        if [ "$(get_service_status "$service_name")" = "active" ]; then
            success "$service_name is running"
        else
            error "$service_name failed to start properly"
            execute_command "sudo systemctl status $service_name --no-pager -l" || true
        fi
    else
        error "Failed to start $service_name"
        return 1
    fi
}

stop_service() {
    local service_name="$1"
    log "Stopping $service_name..."

    if execute_command "sudo systemctl stop $service_name"; then
        success "Stopped $service_name"
    else
        error "Failed to stop $service_name"
        return 1
    fi
}

restart_service() {
    local service_name="$1"
    log "Restarting $service_name..."

    if execute_command "sudo systemctl restart $service_name"; then
        success "Restarted $service_name"
        sleep 2
        if [ "$(get_service_status "$service_name")" = "active" ]; then
            success "$service_name is running"
        else
            error "$service_name failed to restart properly"
            execute_command "sudo systemctl status $service_name --no-pager -l" || true
        fi
    else
        error "Failed to restart $service_name"
        return 1
    fi
}

update_main_service() {
    log "Updating main service configuration..."

    # Kill any processes using port 3000
    log "Checking for processes on port 3000..."
    if execute_command "lsof -ti :3000" >/dev/null 2>&1; then
        warning "Found processes using port 3000, terminating..."
        execute_command "sudo lsof -ti :3000 | xargs -r sudo kill -9" || true
        sleep 2
    fi

    # Update systemd service file if needed
    execute_command "sudo systemctl daemon-reload"

    # Restart the main service
    restart_service "heart-portal-main"

    success "Main service update completed"
}

# Main script logic
ACTION="$1"
SERVICE_FILTER="${2:-}"

case "$ACTION" in
    start)
        if [ -n "$SERVICE_FILTER" ]; then
            # Handle service name variations
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi
            start_service "$SERVICE_FILTER"
        else
            log "Starting all Heart Portal services..."
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                start_service "$service_name"
            done
        fi
        ;;

    stop)
        if [ -n "$SERVICE_FILTER" ]; then
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi
            stop_service "$SERVICE_FILTER"
        else
            log "Stopping all Heart Portal services..."
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                stop_service "$service_name"
            done
        fi
        ;;

    status)
        if [ -n "$SERVICE_FILTER" ]; then
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi
            # Find the port for this service
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                port="${service_def##*:}"
                if [ "$service_name" = "$SERVICE_FILTER" ]; then
                    show_service_status "$service_name" "$port"
                    break
                fi
            done
        else
            log "Heart Portal Service Status:"
            echo
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                port="${service_def##*:}"
                show_service_status "$service_name" "$port"
            done
        fi
        ;;

    restart)
        if [ -n "$SERVICE_FILTER" ]; then
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi
            restart_service "$SERVICE_FILTER"
        else
            log "Restarting all Heart Portal services..."
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                restart_service "$service_name"
            done
        fi
        ;;

    update)
        update_main_service
        ;;

    *)
        error "Invalid action: $ACTION"
        show_usage
        exit 1
        ;;
esac

log "Operation completed successfully"