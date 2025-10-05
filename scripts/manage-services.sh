#!/bin/bash

# Heart Portal Service Management Script
# Consolidates start-system.sh, stop-system.sh, status-system.sh, update-main-service.sh
# Usage: ./manage-services.sh {start|stop|status|restart|update} [service-name] [--local]

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
    "heart-portal-sodium:5003"
    "heart-portal-fluid:5004"
    "heart-portal-weight:5005"
    "heart-portal-bp:5006"
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

# Override run mode if specified
for arg in "$@"; do
    case "$arg" in
        --local)
            RUN_MODE="local"
            SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"
            ;;
    esac
done

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
    echo "Usage: $0 {start|stop|status|restart|update} [service-name] [--local]"
    echo
    echo "Commands:"
    echo "  start    - Start all services or specified service"
    echo "  stop     - Stop all services or specified service"
    echo "  status   - Show status of all services or specified service"
    echo "  restart  - Restart all services or specified service"
    echo "  update   - Update and restart main service"
    echo
    echo "Options:"
    echo "  --local  - Force local mode (manage Flask processes instead of systemd services)"
    echo
    echo "Services:"
    for service_def in "${SERVICES[@]}"; do
        service_name="${service_def%%:*}"
        port="${service_def##*:}"
        echo "  ${service_name##*-} (${service_name}:${port})"
    done
    echo
    echo "Examples:"
    echo "  $0 status                    # Show all service status (remote)"
    echo "  $0 status --local            # Show local Flask process status"
    echo "  $0 restart blog --local      # Restart blog service locally"
    echo "  $0 start heart-portal-blog   # Start blog service (remote)"
    echo "  $0 update                    # Update main service (remote)"
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

# Local Flask process management functions
get_local_service_status() {
    local service_name="$1"
    local port="$2"

    # Check if there's a process running on the port
    if lsof -ti ":$port" >/dev/null 2>&1; then
        echo "active"
    else
        echo "inactive"
    fi
}

show_local_service_status() {
    local service_name="$1"
    local port="$2"
    local status=$(get_local_service_status "$service_name" "$port")
    local service_short="${service_name##*-}"

    if [ "$status" = "active" ]; then
        success "✓ $service_short (port $port) - Running"
        # Show process info
        if pids=$(lsof -ti ":$port" 2>/dev/null); then
            echo "  PID(s): $pids"
        fi
    else
        error "✗ $service_short (port $port) - Stopped"
    fi
}

start_local_service() {
    local service_name="$1"
    local port="$2"
    local service_short="${service_name##*-}"
    local service_dir=""

    # Map service names to directories
    case "$service_short" in
        main) service_dir="main-app" ;;
        blog) service_dir="Blog-Manager" ;;
        nutrition) service_dir="Nutrition-Database" ;;
        food) service_dir="Food-Base" ;;
        sodium) service_dir="Sodium-Tracker" ;;
        fluid) service_dir="Fluid-Tracker" ;;
        weight) service_dir="Weight-Tracker" ;;
        bp) service_dir="BP-Monitor" ;;
        *)
            error "Unknown service: $service_short"
            return 1
            ;;
    esac

    log "Starting $service_short locally..."

    # Check if already running
    if [ "$(get_local_service_status "$service_name" "$port")" = "active" ]; then
        warning "$service_short is already running on port $port"
        return 0
    fi

    # Start the service in the background
    cd "$SCRIPT_DIR/.." || exit 1
    if [ "$service_short" = "main" ]; then
        nohup bash -c "cd $service_dir && REVERSE_PROXY_MODE=true python3 main_app.py" >/dev/null 2>&1 &
    else
        nohup bash -c "cd $service_dir && REVERSE_PROXY_MODE=true python3 app.py" >/dev/null 2>&1 &
    fi

    sleep 2

    if [ "$(get_local_service_status "$service_name" "$port")" = "active" ]; then
        success "Started $service_short on port $port"
    else
        error "Failed to start $service_short"
        return 1
    fi
}

stop_local_service() {
    local service_name="$1"
    local port="$2"
    local service_short="${service_name##*-}"

    log "Stopping $service_short locally..."

    # Check if running
    if [ "$(get_local_service_status "$service_name" "$port")" = "inactive" ]; then
        warning "$service_short is not running"
        return 0
    fi

    # Kill processes using the port
    if pids=$(lsof -ti ":$port" 2>/dev/null); then
        echo "Killing processes: $pids"
        echo $pids | xargs kill -TERM 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if lsof -ti ":$port" >/dev/null 2>&1; then
            echo $pids | xargs kill -9 2>/dev/null || true
        fi
    fi

    if [ "$(get_local_service_status "$service_name" "$port")" = "inactive" ]; then
        success "Stopped $service_short"
    else
        error "Failed to stop $service_short completely"
        return 1
    fi
}

restart_local_service() {
    local service_name="$1"
    local port="$2"

    stop_local_service "$service_name" "$port"
    sleep 1
    start_local_service "$service_name" "$port"
}

# Main script logic - filter out flags from arguments
FILTERED_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --local) ;; # Skip this flag
        *) FILTERED_ARGS+=("$arg") ;;
    esac
done

ACTION="${FILTERED_ARGS[0]:-}"
SERVICE_FILTER="${FILTERED_ARGS[1]:-}"

# Validate that we have an action
if [ -z "$ACTION" ]; then
    error "No action specified"
    show_usage
    exit 1
fi

case "$ACTION" in
    start)
        if [ -n "$SERVICE_FILTER" ]; then
            # Handle service name variations
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi

            if [ "$RUN_MODE" = "local" ]; then
                # Find the port for this service
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    if [ "$service_name" = "$SERVICE_FILTER" ]; then
                        start_local_service "$service_name" "$port"
                        break
                    fi
                done
            else
                start_service "$SERVICE_FILTER"
            fi
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Starting all Heart Portal services locally..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    # Skip nginx for local mode
                    if [[ "$service_name" == "nginx" ]]; then
                        continue
                    fi
                    start_local_service "$service_name" "$port"
                done
            else
                log "Starting all Heart Portal services..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    start_service "$service_name"
                done
            fi
        fi
        ;;

    stop)
        if [ -n "$SERVICE_FILTER" ]; then
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi

            if [ "$RUN_MODE" = "local" ]; then
                # Find the port for this service
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    if [ "$service_name" = "$SERVICE_FILTER" ]; then
                        stop_local_service "$service_name" "$port"
                        break
                    fi
                done
            else
                stop_service "$SERVICE_FILTER"
            fi
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Stopping all Heart Portal services locally..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    # Skip nginx for local mode
                    if [[ "$service_name" == "nginx" ]]; then
                        continue
                    fi
                    stop_local_service "$service_name" "$port"
                done
            else
                log "Stopping all Heart Portal services..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    stop_service "$service_name"
                done
            fi
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
                    if [ "$RUN_MODE" = "local" ]; then
                        show_local_service_status "$service_name" "$port"
                    else
                        show_service_status "$service_name" "$port"
                    fi
                    break
                fi
            done
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Heart Portal Local Service Status:"
            else
                log "Heart Portal Service Status:"
            fi
            echo
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                port="${service_def##*:}"
                # Skip nginx for local mode
                if [ "$RUN_MODE" = "local" ] && [[ "$service_name" == "nginx" ]]; then
                    continue
                fi

                if [ "$RUN_MODE" = "local" ]; then
                    show_local_service_status "$service_name" "$port"
                else
                    show_service_status "$service_name" "$port"
                fi
            done
        fi
        ;;

    restart)
        if [ -n "$SERVICE_FILTER" ]; then
            if [[ "$SERVICE_FILTER" != heart-portal-* ]]; then
                SERVICE_FILTER="heart-portal-$SERVICE_FILTER"
            fi

            if [ "$RUN_MODE" = "local" ]; then
                # Find the port for this service
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    if [ "$service_name" = "$SERVICE_FILTER" ]; then
                        restart_local_service "$service_name" "$port"
                        break
                    fi
                done
            else
                restart_service "$SERVICE_FILTER"
            fi
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Restarting all Heart Portal services locally..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    # Skip nginx for local mode
                    if [[ "$service_name" == "nginx" ]]; then
                        continue
                    fi
                    restart_local_service "$service_name" "$port"
                done
            else
                log "Restarting all Heart Portal services..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    restart_service "$service_name"
                done
            fi
        fi
        ;;

    update)
        if [ "$RUN_MODE" = "local" ]; then
            error "Update command is only available for remote server management"
            echo "Use 'restart main --local' to restart the local main service"
            exit 1
        fi
        update_main_service
        ;;

    *)
        error "Invalid action: $ACTION"
        show_usage
        exit 1
        ;;
esac

log "Operation completed successfully"