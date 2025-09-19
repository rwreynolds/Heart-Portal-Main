#!/bin/bash

# Heart Portal Troubleshooting Script
# Consolidates diagnose-port-3000.sh, safe-server-test.sh, test-solution.sh
# Usage: ./troubleshoot.sh {port|services|ssl|full} [--fix]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_HOST="129.212.181.161"
SERVER_USER="heartportal"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detect run mode
if [ "$(whoami)" = "$SERVER_USER" ] && [ "$(hostname -I 2>/dev/null | grep -q "$SERVER_HOST" && echo "server" || echo "local")" = "server" ]; then
    RUN_MODE="server"
    SSH_CMD=""
else
    RUN_MODE="local"
    SSH_CMD="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST"
fi

AUTO_FIX=false
for arg in "$@"; do
    if [ "$arg" = "--fix" ]; then
        AUTO_FIX=true
        break
    fi
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

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
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
    echo "Usage: $0 {port|services|ssl|full} [--fix]"
    echo
    echo "Diagnostics:"
    echo "  port      - Diagnose port 3000 conflicts and issues"
    echo "  services  - Test all Heart Portal services"
    echo "  ssl       - Comprehensive SSL/HTTPS testing"
    echo "  full      - Complete system diagnostic"
    echo
    echo "Options:"
    echo "  --fix     - Attempt automatic fixes for detected issues"
    echo
    echo "Examples:"
    echo "  $0 port --fix              # Diagnose and fix port 3000 issues"
    echo "  $0 services                # Test all services"
    echo "  $0 ssl                     # Check SSL configuration"
    echo "  $0 full                    # Run complete diagnostic"
}

# Port 3000 Diagnostics
diagnose_port_3000() {
    log "=== Port 3000 Diagnostic ==="
    echo

    # Check if port is in use
    info "Checking port 3000 usage..."
    local port_processes
    port_processes=$(execute_command "lsof -ti :3000" 2>/dev/null || echo "")

    if [ -z "$port_processes" ]; then
        success "Port 3000 is available"
    else
        warning "Port 3000 is in use by the following processes:"
        execute_command "lsof -i :3000" || true

        if [ "$AUTO_FIX" = true ]; then
            warning "Attempting to free port 3000..."
            execute_command "sudo lsof -ti :3000 | xargs -r sudo kill -9" || true
            sleep 2

            port_processes=$(execute_command "lsof -ti :3000" 2>/dev/null || echo "")
            if [ -z "$port_processes" ]; then
                success "Port 3000 freed successfully"
            else
                error "Failed to free port 3000"
            fi
        fi
    fi

    # Check heart-portal-main service
    info "Checking heart-portal-main service..."
    if execute_command "systemctl is-active heart-portal-main" >/dev/null 2>&1; then
        success "heart-portal-main service is active"
    else
        warning "heart-portal-main service is not active"
        execute_command "systemctl status heart-portal-main --no-pager -l" || true

        if [ "$AUTO_FIX" = true ]; then
            warning "Attempting to start heart-portal-main service..."
            if execute_command "sudo systemctl start heart-portal-main"; then
                success "Service started successfully"
            else
                error "Failed to start service"
            fi
        fi
    fi

    # Test connectivity
    info "Testing port 3000 connectivity..."
    if execute_command "nc -z localhost 3000" >/dev/null 2>&1; then
        success "Port 3000 is responding"

        # Test HTTP response
        local response_code
        response_code=$(execute_command "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/" || echo "000")
        if [ "$response_code" = "200" ]; then
            success "HTTP response: $response_code OK"
        else
            warning "HTTP response: $response_code"
        fi
    else
        error "Port 3000 is not responding"
    fi
}

# Service Diagnostics
diagnose_services() {
    log "=== Service Diagnostics ==="
    echo

    local services=(
        "heart-portal-main:3000"
        "heart-portal-nutrition:5000"
        "heart-portal-food:5001"
        "heart-portal-blog:5002"
        "nginx:80,443"
    )

    for service_def in "${services[@]}"; do
        service_name="${service_def%%:*}"
        ports="${service_def##*:}"
        main_port="${ports%%,*}"

        info "Testing $service_name..."

        # Check systemctl status
        if execute_command "systemctl is-active $service_name" >/dev/null 2>&1; then
            success "✓ $service_name - Service active"
        else
            error "✗ $service_name - Service inactive"
            if [ "$AUTO_FIX" = true ]; then
                warning "Attempting to start $service_name..."
                execute_command "sudo systemctl start $service_name" || true
            fi
            continue
        fi

        # Check port connectivity
        if execute_command "nc -z localhost $main_port" >/dev/null 2>&1; then
            success "✓ Port $main_port - Responding"
        else
            error "✗ Port $main_port - Not responding"
        fi

        # Test HTTP endpoints (skip nginx)
        if [ "$service_name" != "nginx" ]; then
            local endpoint="http://localhost:$main_port/"
            local response_code
            response_code=$(execute_command "curl -s -o /dev/null -w '%{http_code}' --max-time 10 $endpoint" || echo "000")

            if [ "$response_code" = "200" ]; then
                success "✓ HTTP response - 200 OK"
            else
                warning "⚠ HTTP response - $response_code"
            fi
        fi

        echo
    done
}

# SSL Diagnostics
diagnose_ssl() {
    log "=== SSL/HTTPS Diagnostics ==="
    echo

    local domain="heartfailureportal.com"

    # Check nginx status
    info "Checking nginx status..."
    if execute_command "systemctl is-active nginx" >/dev/null 2>&1; then
        success "✓ Nginx is running"
    else
        error "✗ Nginx is not running"
        if [ "$AUTO_FIX" = true ]; then
            warning "Attempting to start nginx..."
            execute_command "sudo systemctl start nginx" || true
        fi
        return 1
    fi

    # Check SSL certificate files
    info "Checking SSL certificate files..."
    if execute_command "test -f /etc/letsencrypt/live/$domain/fullchain.pem"; then
        success "✓ SSL certificate exists"

        # Check certificate validity
        local expiry_days
        expiry_days=$(execute_command "openssl x509 -in /etc/letsencrypt/live/$domain/fullchain.pem -noout -checkend 2592000" >/dev/null 2>&1 && echo "30+" || echo "<30")
        if [ "$expiry_days" = "30+" ]; then
            success "✓ Certificate valid for 30+ days"
        else
            warning "⚠ Certificate expires within 30 days"
        fi
    else
        error "✗ SSL certificate not found"
        if [ "$AUTO_FIX" = true ]; then
            warning "SSL certificate missing - manual intervention required"
            info "Run: sudo certbot --nginx -d $domain"
        fi
        return 1
    fi

    # Test HTTPS connectivity
    info "Testing HTTPS connectivity..."
    if execute_command "curl -I https://$domain" >/dev/null 2>&1; then
        success "✓ HTTPS is accessible"

        # Test redirect
        local redirect_response
        redirect_response=$(execute_command "curl -s -o /dev/null -w '%{http_code}' http://$domain" || echo "000")
        if [ "$redirect_response" = "301" ] || [ "$redirect_response" = "302" ]; then
            success "✓ HTTP to HTTPS redirect working"
        else
            warning "⚠ HTTP redirect response: $redirect_response"
        fi
    else
        error "✗ HTTPS not accessible"
    fi

    # Test SSL grade
    info "Checking SSL configuration..."
    local ssl_grade
    ssl_grade=$(execute_command "echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -text | grep 'Signature Algorithm' | head -1" || echo "unknown")
    if [[ "$ssl_grade" == *"sha256"* ]]; then
        success "✓ SSL using secure signature algorithm"
    else
        warning "⚠ SSL signature algorithm: $ssl_grade"
    fi
}

# Network Diagnostics
diagnose_network() {
    log "=== Network Diagnostics ==="
    echo

    # Check firewall status
    info "Checking firewall status..."
    if execute_command "ufw status" | grep -q "Status: active"; then
        success "✓ UFW firewall is active"

        # Check important ports
        local important_ports=("22" "80" "443" "3000" "5000" "5001" "5002")
        for port in "${important_ports[@]}"; do
            if execute_command "ufw status" | grep -q "$port"; then
                success "✓ Port $port allowed in firewall"
            else
                warning "⚠ Port $port not explicitly allowed"
            fi
        done
    else
        warning "⚠ UFW firewall is inactive"
    fi

    # Check external connectivity
    info "Testing external connectivity..."
    if execute_command "ping -c 1 8.8.8.8" >/dev/null 2>&1; then
        success "✓ External connectivity working"
    else
        error "✗ External connectivity failed"
    fi

    # Check DNS resolution
    info "Testing DNS resolution..."
    if execute_command "nslookup heartfailureportal.com" >/dev/null 2>&1; then
        success "✓ DNS resolution working"
    else
        error "✗ DNS resolution failed"
    fi
}

# System Health Check
check_system_health() {
    log "=== System Health Check ==="
    echo

    # Check disk space
    info "Checking disk space..."
    local disk_usage
    disk_usage=$(execute_command "df / | awk 'NR==2 {print \$5}' | sed 's/%//'")
    if [ "$disk_usage" -lt 80 ]; then
        success "✓ Disk usage: ${disk_usage}% (healthy)"
    elif [ "$disk_usage" -lt 90 ]; then
        warning "⚠ Disk usage: ${disk_usage}% (concerning)"
    else
        error "✗ Disk usage: ${disk_usage}% (critical)"
    fi

    # Check memory usage
    info "Checking memory usage..."
    local memory_usage
    memory_usage=$(execute_command "free | awk 'NR==2{printf \"%.0f\", \$3*100/\$2}'")
    if [ "$memory_usage" -lt 80 ]; then
        success "✓ Memory usage: ${memory_usage}% (healthy)"
    elif [ "$memory_usage" -lt 90 ]; then
        warning "⚠ Memory usage: ${memory_usage}% (concerning)"
    else
        error "✗ Memory usage: ${memory_usage}% (critical)"
    fi

    # Check system load
    info "Checking system load..."
    local load_avg
    load_avg=$(execute_command "uptime | awk -F'load average:' '{print \$2}' | awk '{print \$1}' | sed 's/,//'")
    success "✓ System load: $load_avg"

    # Check for recent errors in logs
    info "Checking recent system errors..."
    local error_count
    error_count=$(execute_command "journalctl --since '1 hour ago' --priority=err | wc -l" || echo "0")
    if [ "$error_count" -eq 0 ]; then
        success "✓ No recent system errors"
    else
        warning "⚠ $error_count system errors in the last hour"
    fi
}

# Full diagnostic
run_full_diagnostic() {
    log "=== Heart Portal Full System Diagnostic ==="
    echo

    check_system_health
    echo
    diagnose_services
    echo
    diagnose_port_3000
    echo
    diagnose_ssl
    echo
    diagnose_network

    log "=== Diagnostic Summary ==="
    echo
    info "Run mode: $RUN_MODE"
    info "Auto-fix: $AUTO_FIX"
    success "Full diagnostic completed"
}

# Main script logic
ACTION="${1:-full}"

case "$ACTION" in
    port)
        diagnose_port_3000
        ;;
    services)
        diagnose_services
        ;;
    ssl)
        diagnose_ssl
        ;;
    network)
        diagnose_network
        ;;
    system)
        check_system_health
        ;;
    full)
        run_full_diagnostic
        ;;
    *)
        error "Invalid action: $ACTION"
        show_usage
        exit 1
        ;;
esac

log "Troubleshooting completed"