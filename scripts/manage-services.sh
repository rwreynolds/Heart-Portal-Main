#!/bin/bash

# Heart Portal Service Management Script
# Consolidates start-system.sh, stop-system.sh, status-system.sh, update-main-service.sh
# Usage: ./manage-services.sh {start|stop|status|restart|update} [service-name] [--local|--staging]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default to production server
SERVER_HOST="129.212.181.161"
SERVER_USER="heartportal"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"
SERVICE_PREFIX="heart-portal"

# Service definitions (will be prefixed with staging if --staging is used)
SERVICES=(
    "main:3000"
    "nutrition:5000"
    "food:5001"
    "blog:5002"
    "sodium:5003"
    "fluid:5004"
    "weight:5005"
    "bp:5006"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default to remote mode (managing systemd services via SSH)
RUN_MODE="remote"
SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"

# Check if we're running on the server itself
if [ "$(whoami)" = "$SERVER_USER" ]; then
    RUN_MODE="server"
    SSH_CMD=""
fi

# Override run mode, service prefix, and server if specified
for arg in "$@"; do
    case "$arg" in
        --local)
            RUN_MODE="local"
            ;;
        --staging)
            # Switch to staging server
            SERVER_HOST="134.199.202.67"
            SSH_KEY="/Users/mrrobot/.ssh/id_HFP_staging"
            SERVICE_PREFIX="heart-portal-staging"
            # Update SSH command for staging server
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
        # Local mode: manage local Flask processes
        eval "$cmd"
    elif [ "$RUN_MODE" = "remote" ]; then
        # Remote mode: manage remote systemd services via SSH
        $SSH_CMD "$cmd"
    else
        # Server mode: running on the server itself
        eval "$cmd"
    fi
}

show_usage() {
    echo "Usage: $0 {start|stop|status|restart|update} [service-name] [--local|--staging]"
    echo
    echo "Commands:"
    echo "  start    - Start all services or specified service"
    echo "  stop     - Stop all services or specified service"
    echo "  status   - Show status of all services or specified service"
    echo "  restart  - Restart all services or specified service"
    echo "  update   - Update and restart main service"
    echo
    echo "Options:"
    echo "  --local    - Force local mode (manage Flask processes instead of systemd services)"
    echo "  --staging  - Manage staging services (heart-portal-staging-*)"
    echo
    echo "Services:"
    for service_def in "${SERVICES[@]}"; do
        service_name="${service_def%%:*}"
        port="${service_def##*:}"
        echo "  $service_name (port $port)"
    done
    echo
    echo "Examples:"
    echo "  $0 status                      # Show all production service status"
    echo "  $0 status --staging            # Show all staging service status"
    echo "  $0 restart --staging           # Restart all staging services"
    echo "  $0 restart blog --staging      # Restart blog staging service"
    echo "  $0 status --local              # Show local Flask process status"
    echo "  $0 restart blog --local        # Restart blog service locally"
    echo "  $0 update                      # Update main production service"
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
        --local|--staging) ;; # Skip these flags
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
            # Build full service name with prefix
            FULL_SERVICE_NAME="${SERVICE_PREFIX}-${SERVICE_FILTER}"

            if [ "$RUN_MODE" = "local" ]; then
                # Find the port for this service
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    if [ "$service_name" = "$SERVICE_FILTER" ]; then
                        start_local_service "${SERVICE_PREFIX}-${service_name}" "$port"
                        break
                    fi
                done
            else
                start_service "$FULL_SERVICE_NAME"
            fi
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Starting all Heart Portal services locally..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    start_local_service "${SERVICE_PREFIX}-${service_name}" "$port"
                done
            else
                log "Starting all $SERVICE_PREFIX services..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    start_service "${SERVICE_PREFIX}-${service_name}"
                done
            fi
        fi
        ;;

    stop)
        if [ -n "$SERVICE_FILTER" ]; then
            FULL_SERVICE_NAME="${SERVICE_PREFIX}-${SERVICE_FILTER}"

            if [ "$RUN_MODE" = "local" ]; then
                # Find the port for this service
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    if [ "$service_name" = "$SERVICE_FILTER" ]; then
                        stop_local_service "${SERVICE_PREFIX}-${service_name}" "$port"
                        break
                    fi
                done
            else
                stop_service "$FULL_SERVICE_NAME"
            fi
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Stopping all Heart Portal services locally..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    stop_local_service "${SERVICE_PREFIX}-${service_name}" "$port"
                done
            else
                log "Stopping all $SERVICE_PREFIX services..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    stop_service "${SERVICE_PREFIX}-${service_name}"
                done
            fi
        fi
        ;;

    status)
        if [ -n "$SERVICE_FILTER" ]; then
            FULL_SERVICE_NAME="${SERVICE_PREFIX}-${SERVICE_FILTER}"
            # Find the port for this service
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                port="${service_def##*:}"
                if [ "$service_name" = "$SERVICE_FILTER" ]; then
                    if [ "$RUN_MODE" = "local" ]; then
                        show_local_service_status "${SERVICE_PREFIX}-${service_name}" "$port"
                    else
                        show_service_status "$FULL_SERVICE_NAME" "$port"
                    fi
                    break
                fi
            done
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Heart Portal Local Service Status:"
            else
                log "$SERVICE_PREFIX Service Status:"
            fi
            echo
            for service_def in "${SERVICES[@]}"; do
                service_name="${service_def%%:*}"
                port="${service_def##*:}"

                if [ "$RUN_MODE" = "local" ]; then
                    show_local_service_status "${SERVICE_PREFIX}-${service_name}" "$port"
                else
                    show_service_status "${SERVICE_PREFIX}-${service_name}" "$port"
                fi
            done
        fi
        ;;

    restart)
        if [ -n "$SERVICE_FILTER" ]; then
            FULL_SERVICE_NAME="${SERVICE_PREFIX}-${SERVICE_FILTER}"

            if [ "$RUN_MODE" = "local" ]; then
                # Find the port for this service
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    if [ "$service_name" = "$SERVICE_FILTER" ]; then
                        restart_local_service "${SERVICE_PREFIX}-${service_name}" "$port"
                        break
                    fi
                done
            else
                restart_service "$FULL_SERVICE_NAME"
            fi
        else
            if [ "$RUN_MODE" = "local" ]; then
                log "Restarting all Heart Portal services locally..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    port="${service_def##*:}"
                    restart_local_service "${SERVICE_PREFIX}-${service_name}" "$port"
                done
            else
                log "Restarting all $SERVICE_PREFIX services..."
                for service_def in "${SERVICES[@]}"; do
                    service_name="${service_def%%:*}"
                    restart_service "${SERVICE_PREFIX}-${service_name}"
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