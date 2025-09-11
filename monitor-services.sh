#!/bin/bash

# Heart Portal Service Monitor
# Monitors all services including Nginx and provides health checks

set -e

# Colors
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

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

check_service() {
    local service=$1
    local description=$2
    
    if systemctl is-active --quiet "$service"; then
        success "$description is running"
        return 0
    else
        error "$description is not running"
        return 1
    fi
}

check_port() {
    local port=$1
    local service=$2
    
    if ss -tuln | grep -q ":$port "; then
        success "$service (port $port) is listening"
        return 0
    else
        error "$service (port $port) is not responding"
        return 1
    fi
}

check_https() {
    local domain=$1
    local path=${2:-"/health"}
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain$path" || echo "000")
    
    if [ "$response_code" = "200" ]; then
        success "HTTPS $domain$path is responding"
        return 0
    else
        error "HTTPS $domain$path returned $response_code"
        return 1
    fi
}

check_ssl_certificate() {
    local domain=$1
    
    if [ ! -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
        error "SSL certificate for $domain not found"
        return 1
    fi
    
    local cert_expire=$(openssl x509 -in /etc/letsencrypt/live/$domain/fullchain.pem -noout -dates | grep notAfter | cut -d= -f2)
    local expire_timestamp=$(date -d "$cert_expire" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expire=$(( (expire_timestamp - current_timestamp) / 86400 ))
    
    if [ $days_until_expire -gt 30 ]; then
        success "SSL certificate valid for $days_until_expire days"
        return 0
    elif [ $days_until_expire -gt 7 ]; then
        warning "SSL certificate expires in $days_until_expire days"
        return 0
    else
        error "SSL certificate expires in $days_until_expire days - renewal needed!"
        return 1
    fi
}

main() {
    echo "========================================"
    echo "📊 Heart Portal Health Check"
    echo "========================================"
    echo
    
    local all_good=true
    
    # Check systemd services
    log "Checking systemd services..."
    check_service "heart-portal-main" "Main App" || all_good=false
    check_service "heart-portal-nutrition" "Nutrition Database" || all_good=false
    check_service "heart-portal-food" "Food Base" || all_good=false
    check_service "heart-portal-blog" "Blog Manager" || all_good=false
    check_service "nginx" "Nginx Reverse Proxy" || all_good=false
    echo
    
    # Check listening ports
    log "Checking service ports..."
    check_port "3000" "Main App" || all_good=false
    check_port "5000" "Nutrition Database" || all_good=false
    check_port "5001" "Food Base" || all_good=false
    check_port "5002" "Blog Manager" || all_good=false
    check_port "80" "Nginx HTTP" || all_good=false
    check_port "443" "Nginx HTTPS" || all_good=false
    echo
    
    # Check HTTPS endpoints
    log "Checking HTTPS endpoints..."
    check_https "heartfailureportal.com" "/" || all_good=false
    check_https "heartfailureportal.com" "/health" || all_good=false
    check_https "heartfailureportal.com" "/nutrition-database/" || all_good=false
    check_https "heartfailureportal.com" "/food-base/" || all_good=false
    check_https "heartfailureportal.com" "/blog-manager/" || all_good=false
    echo
    
    # Check SSL certificate
    log "Checking SSL certificate..."
    check_ssl_certificate "heartfailureportal.com" || all_good=false
    echo
    
    # Overall status
    if [ "$all_good" = true ]; then
        success "🎉 All services are healthy!"
    else
        error "⚠️  Some services need attention"
        echo
        echo "🔧 Troubleshooting commands:"
        echo "  systemctl status heart-portal-* nginx"
        echo "  journalctl -u heart-portal-main -f"
        echo "  tail -f /var/log/nginx/error.log"
        echo "  certbot certificates"
        exit 1
    fi
}

case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Service Monitor"
        echo
        echo "Usage: ./monitor-services.sh [options]"
        echo
        echo "This script checks the health of all Heart Portal services including:"
        echo "- Systemd service status"
        echo "- Port connectivity"
        echo "- HTTPS endpoints"
        echo "- SSL certificate validity"
        echo
        ;;
    *)
        main "$@"
        ;;
esac