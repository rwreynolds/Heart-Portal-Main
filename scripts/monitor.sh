#!/bin/bash

# Heart Portal Monitoring Script
# Consolidates monitor-services.sh and monitor-main-app.sh
# Usage: ./monitor.sh {all|main|continuous} [--local|--remote]

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
    "nginx:80,443"
)

# Monitoring configuration
MONITORING_INTERVAL=30
MAX_RESTART_ATTEMPTS=3
RESTART_WINDOW=300
HEALTH_CHECK_TIMEOUT=10
ALERT_COOLDOWN=300

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect run mode
if [ "$(whoami)" = "$SERVER_USER" ] && [ "$(hostname -I 2>/dev/null | grep -q "$SERVER_HOST" && echo "server" || echo "local")" = "server" ]; then
    RUN_MODE="server"
    SSH_CMD=""
    LOG_FILE="/var/log/heart-portal-monitoring.log"
    ALERT_LOG="/var/log/heart-portal-alerts.log"
    PID_FILE="/var/run/heart-portal-monitor.pid"
else
    RUN_MODE="local"
    SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"
    LOG_FILE="/tmp/heart-portal-monitoring.log"
    ALERT_LOG="/tmp/heart-portal-alerts.log"
    PID_FILE="/tmp/heart-portal-monitor.pid"
fi

# Override run mode and server if specified
for arg in "$@"; do
    case "$arg" in
        --local)
            RUN_MODE="local"
            SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"
            ;;
        --remote)
            RUN_MODE="server"
            SSH_CMD=""
            ;;
        --staging)
            # Switch to staging server
            SERVER_HOST="134.199.202.67"
            SSH_KEY="/Users/mrrobot/.ssh/id_HFP_staging"
            SERVICE_PREFIX="heart-portal-staging"
            RUN_MODE="local"
            SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"
            ;;
    esac
done

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}${message}${NC}"
    if [ -w "$(dirname "$LOG_FILE")" ] 2>/dev/null; then
        echo "$message" >> "$LOG_FILE"
    fi
}

error() {
    local message="[ERROR] $1"
    echo -e "${RED}${message}${NC}" >&2
    if [ -w "$(dirname "$LOG_FILE")" ] 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$LOG_FILE"
    fi
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    local message="[WARNING] $1"
    echo -e "${YELLOW}${message}${NC}"
    if [ -w "$(dirname "$LOG_FILE")" ] 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$LOG_FILE"
    fi
}

execute_command() {
    local cmd="$1"
    if [ "$RUN_MODE" = "local" ]; then
        $SSH_CMD "$cmd" 2>/dev/null
    else
        # When in server/remote mode, ensure we're actually running on server
        if [ "$(whoami)" != "$SERVER_USER" ]; then
            # If not on server, execute via SSH anyway
            ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "$cmd" 2>/dev/null
        else
            eval "$cmd" 2>/dev/null
        fi
    fi
}

show_usage() {
    echo "Usage: $0 {all|main|continuous} [--local|--remote]"
    echo
    echo "Commands:"
    echo "  all        - Show status of all services once"
    echo "  main       - Show detailed status of main app only"
    echo "  continuous - Start continuous monitoring with auto-restart"
    echo
    echo "Options:"
    echo "  --local    - Force local mode (monitor remote server via SSH)"
    echo "  --remote   - Force remote mode (run directly on server)"
    echo
    echo "Examples:"
    echo "  $0 all                       # Quick status check"
    echo "  $0 main --local              # Check main app from local machine"
    echo "  $0 continuous                # Start continuous monitoring"
}

check_service_health() {
    local service_name="$1"
    local port="$2"
    local health_score=0

    # Check systemctl status
    if execute_command "systemctl is-active $service_name" >/dev/null 2>&1; then
        ((health_score += 40))
    fi

    # Check port connectivity
    if execute_command "nc -z localhost $port" >/dev/null 2>&1; then
        ((health_score += 30))
    fi

    # Check process exists
    if execute_command "pgrep -f $service_name" >/dev/null 2>&1; then
        ((health_score += 20))
    fi

    # Check recent logs for errors (no errors = good = +10 points)
    if ! execute_command "journalctl -u $service_name --since '5 minutes ago' -q 2>/dev/null | grep -i error" >/dev/null 2>&1; then
        ((health_score += 10))
    fi

    echo $health_score
}

check_ssl_status() {
    local domain="heartfailureportal.com"

    if execute_command "curl -I https://$domain" >/dev/null 2>&1; then
        success "✓ SSL Certificate - Valid"

        # Check certificate expiry
        local expiry_date
        expiry_date=$(execute_command "echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2")

        if [ -n "$expiry_date" ]; then
            echo "  Certificate expires: $expiry_date"
        fi
    else
        error "✗ SSL Certificate - Invalid or unreachable"
    fi
}

show_service_status() {
    local service_name="$1"
    local ports="$2"
    local health_score
    local pid_info=""

    # Handle multiple ports
    local main_port="${ports%%,*}"
    health_score=$(check_service_health "$service_name" "$main_port")

    # Get PID information for the main port
    local pids
    pids=$(execute_command "lsof -ti :$main_port 2>/dev/null" || echo "")
    if [ -n "$pids" ]; then
        # Handle multiple PIDs by taking the first one and counting total
        local first_pid=$(echo "$pids" | head -n1)
        local pid_count=$(echo "$pids" | wc -l | tr -d ' ')
        if [ "$pid_count" -eq 1 ]; then
            pid_info=" [PID: $first_pid]"
        else
            pid_info=" [PIDs: $first_pid +$(($pid_count - 1)) more]"
        fi
    else
        pid_info=" [No PID]"
    fi

    if [ "$health_score" -ge 70 ]; then
        success "✓ $service_name (ports: $ports)$pid_info - Healthy ($health_score%)"
    elif [ "$health_score" -ge 40 ]; then
        warning "⚠ $service_name (ports: $ports)$pid_info - Degraded ($health_score%)"
    else
        error "✗ $service_name (ports: $ports)$pid_info - Unhealthy ($health_score%)"
    fi

    # Show additional details for main app
    if [ "$service_name" = "${SERVICE_PREFIX}-main" ]; then
        show_main_app_details
    fi
}

show_main_app_details() {
    local port=3000

    # Check for port conflicts
    local port_processes
    port_processes=$(execute_command "lsof -ti :$port" || echo "")

    if [ -n "$port_processes" ]; then
        local process_count
        process_count=$(echo "$port_processes" | wc -l)
        if [ "$process_count" -gt 1 ]; then
            warning "  Multiple processes detected on port $port"
            execute_command "lsof -i :$port" || true
        fi
    fi

    # Check memory usage
    local memory_usage
    memory_usage=$(execute_command "ps aux | grep '[p]ython.*main_app' | awk '{print \$4}'" || echo "0")
    if [ -n "$memory_usage" ] && [ "$memory_usage" != "0" ]; then
        echo "  Memory usage: ${memory_usage}%"
    fi

    # Check response time
    local response_time
    response_time=$(execute_command "curl -o /dev/null -s -w '%{time_total}' http://localhost:$port/" || echo "timeout")
    if [ "$response_time" != "timeout" ]; then
        echo "  Response time: ${response_time}s"
    else
        warning "  Response timeout"
    fi
}

restart_service_with_backoff() {
    local service_name="$1"
    local attempt_file="/tmp/${service_name}_restart_attempts"
    local current_time=$(date +%s)

    # Clean old attempt records
    if [ -f "$attempt_file" ]; then
        local file_time
        file_time=$(stat -c %Y "$attempt_file" 2>/dev/null || stat -f %m "$attempt_file" 2>/dev/null || echo 0)
        if [ $((current_time - file_time)) -gt $RESTART_WINDOW ]; then
            rm -f "$attempt_file"
        fi
    fi

    # Count recent attempts
    local attempts=1
    if [ -f "$attempt_file" ]; then
        attempts=$(cat "$attempt_file")
        ((attempts++))
    fi

    if [ $attempts -le $MAX_RESTART_ATTEMPTS ]; then
        warning "Attempting restart of $service_name (attempt $attempts/$MAX_RESTART_ATTEMPTS)"

        if execute_command "sudo systemctl restart $service_name"; then
            success "Successfully restarted $service_name"
            rm -f "$attempt_file"
            return 0
        else
            echo $attempts > "$attempt_file"
            error "Failed to restart $service_name (attempt $attempts)"
            return 1
        fi
    else
        error "$service_name has exceeded maximum restart attempts ($MAX_RESTART_ATTEMPTS)"

        # Log alert
        if [ -w "$(dirname "$ALERT_LOG")" ] 2>/dev/null; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRITICAL: $service_name exceeded restart attempts" >> "$ALERT_LOG"
        fi

        return 1
    fi
}

continuous_monitoring() {
    log "Starting continuous monitoring (interval: ${MONITORING_INTERVAL}s)"

    # Save PID
    if [ -w "$(dirname "$PID_FILE")" ] 2>/dev/null; then
        echo $$ > "$PID_FILE"
    fi

    trap 'log "Monitoring stopped"; rm -f "$PID_FILE"; exit 0' INT TERM

    while true; do
        log "Running health check cycle..."

        for service_def in "${SERVICES[@]}"; do
            if [ "$service_def" = "nginx:80,443" ]; then
                continue  # Skip nginx for auto-restart
            fi

            service_short="${service_def%%:*}"
            service_name="${SERVICE_PREFIX}-${service_short}"
            ports="${service_def##*:}"
            main_port="${ports%%,*}"

            health_score=$(check_service_health "$service_name" "$main_port")

            if [ "$health_score" -lt 40 ]; then
                warning "$service_name is unhealthy (score: $health_score)"
                restart_service_with_backoff "$service_name"
            else
                log "$service_name is healthy (score: $health_score)"
            fi
        done

        sleep $MONITORING_INTERVAL
    done
}

# Main script logic
ACTION="${1:-all}"

case "$ACTION" in
    all)
        log "Heart Portal Service Monitor ($RUN_MODE mode)"
        echo

        for service_def in "${SERVICES[@]}"; do
            service_short="${service_def%%:*}"
            # nginx doesn't need prefix
            if [ "$service_short" = "nginx" ]; then
                service_name="nginx"
            else
                service_name="${SERVICE_PREFIX}-${service_short}"
            fi
            ports="${service_def##*:}"
            show_service_status "$service_name" "$ports"
        done

        echo
        check_ssl_status
        ;;

    main)
        log "Heart Portal Main App Monitor ($RUN_MODE mode)"
        echo
        show_service_status "${SERVICE_PREFIX}-main" "3000"
        ;;

    continuous)
        if [ "$RUN_MODE" = "local" ]; then
            error "Continuous monitoring should be run on the server"
            echo "Use: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST '$0 continuous --remote'"
            exit 1
        fi
        continuous_monitoring
        ;;

    *)
        error "Invalid action: $ACTION"
        show_usage
        exit 1
        ;;
esac