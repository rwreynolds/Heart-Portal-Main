#!/bin/bash

# Heart Portal SSL Testing Script
# Comprehensive SSL/HTTPS testing for all endpoints

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

DOMAIN="heartfailureportal.com"
WWW_DOMAIN="www.heartfailureportal.com"

test_ssl_certificate() {
    log "Testing SSL certificate configuration..."
    
    # Check if certificate files exist
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        success "Certificate files found"
    else
        error "Certificate files not found"
        return 1
    fi
    
    # Check certificate validity
    local cert_info=$(openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -subject -dates -issuer)
    echo "$cert_info"
    
    # Check expiry
    local cert_expire=$(openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -dates | grep notAfter | cut -d= -f2)
    local expire_timestamp=$(date -d "$cert_expire" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expire=$(( (expire_timestamp - current_timestamp) / 86400 ))
    
    if [ $days_until_expire -gt 7 ]; then
        success "Certificate valid for $days_until_expire days"
    else
        warning "Certificate expires in $days_until_expire days"
    fi
}

test_https_endpoint() {
    local url=$1
    local expected_code=${2:-200}
    local description=$3
    
    log "Testing $description: $url"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code};REDIRECT:%{redirect_url};TIME:%{time_total}" "$url" -o /dev/null)
    
    local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local redirect_url=$(echo "$response" | grep -o "REDIRECT:[^;]*" | cut -d: -f2-)
    local response_time=$(echo "$response" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    
    if [ "$http_code" = "$expected_code" ]; then
        success "$description responded with $http_code in ${response_time}s"
    else
        error "$description responded with $http_code (expected $expected_code)"
        if [ -n "$redirect_url" ] && [ "$redirect_url" != "" ]; then
            log "Redirect URL: $redirect_url"
        fi
        return 1
    fi
}

test_ssl_connection() {
    local domain=$1
    local port=${2:-443}
    
    log "Testing SSL connection to $domain:$port"
    
    # Test SSL handshake
    if timeout 10 openssl s_client -connect "$domain:$port" -servername "$domain" </dev/null > /dev/null 2>&1; then
        success "SSL handshake successful"
    else
        error "SSL handshake failed"
        return 1
    fi
    
    # Get SSL details
    local ssl_info=$(timeout 10 openssl s_client -connect "$domain:$port" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>/dev/null || echo "Failed to get SSL info")
    echo "$ssl_info"
}

test_security_headers() {
    local url=$1
    
    log "Testing security headers for $url"
    
    local headers=$(curl -s -I "$url")
    
    # Check for important security headers
    local security_score=0
    local total_checks=6
    
    if echo "$headers" | grep -i "X-Frame-Options" > /dev/null; then
        success "X-Frame-Options header present"
        ((security_score++))
    else
        warning "X-Frame-Options header missing"
    fi
    
    if echo "$headers" | grep -i "X-Content-Type-Options" > /dev/null; then
        success "X-Content-Type-Options header present"
        ((security_score++))
    else
        warning "X-Content-Type-Options header missing"
    fi
    
    if echo "$headers" | grep -i "X-XSS-Protection" > /dev/null; then
        success "X-XSS-Protection header present"
        ((security_score++))
    else
        warning "X-XSS-Protection header missing"
    fi
    
    if echo "$headers" | grep -i "Referrer-Policy" > /dev/null; then
        success "Referrer-Policy header present"
        ((security_score++))
    else
        warning "Referrer-Policy header missing"
    fi
    
    if echo "$headers" | grep -i "Strict-Transport-Security" > /dev/null; then
        success "HSTS header present"
        ((security_score++))
    else
        warning "HSTS header missing (may be added by certbot)"
    fi
    
    if echo "$headers" | grep -i "Content-Security-Policy" > /dev/null; then
        success "CSP header present"
        ((security_score++))
    else
        warning "Content-Security-Policy header missing"
    fi
    
    log "Security headers score: $security_score/$total_checks"
}

test_http_redirect() {
    local domain=$1
    
    log "Testing HTTP to HTTPS redirect for $domain"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code};REDIRECT:%{redirect_url}" "http://$domain/" -o /dev/null)
    local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local redirect_url=$(echo "$response" | grep -o "REDIRECT:[^;]*" | cut -d: -f2-)
    
    if [ "$http_code" = "301" ] || [ "$http_code" = "302" ]; then
        if echo "$redirect_url" | grep -q "https://"; then
            success "HTTP redirects to HTTPS ($http_code)"
        else
            warning "HTTP redirects but not to HTTPS: $redirect_url"
        fi
    else
        error "HTTP does not redirect to HTTPS (code: $http_code)"
        return 1
    fi
}

test_performance() {
    local url=$1
    
    log "Testing performance for $url"
    
    local response=$(curl -s -w "TIME_NAMELOOKUP:%{time_namelookup};TIME_CONNECT:%{time_connect};TIME_APPCONNECT:%{time_appconnect};TIME_PRETRANSFER:%{time_pretransfer};TIME_REDIRECT:%{time_redirect};TIME_STARTTRANSFER:%{time_starttransfer};TIME_TOTAL:%{time_total}" "$url" -o /dev/null)
    
    local time_namelookup=$(echo "$response" | grep -o "TIME_NAMELOOKUP:[0-9.]*" | cut -d: -f2)
    local time_connect=$(echo "$response" | grep -o "TIME_CONNECT:[0-9.]*" | cut -d: -f2)
    local time_appconnect=$(echo "$response" | grep -o "TIME_APPCONNECT:[0-9.]*" | cut -d: -f2)
    local time_total=$(echo "$response" | grep -o "TIME_TOTAL:[0-9.]*" | cut -d: -f2)
    
    echo "  DNS Lookup:    ${time_namelookup}s"
    echo "  TCP Connect:   ${time_connect}s"
    echo "  SSL Connect:   ${time_appconnect}s"
    echo "  Total Time:    ${time_total}s"
    
    # Warn if too slow
    if (( $(echo "$time_total > 5.0" | bc -l) )); then
        warning "Response time is slow (${time_total}s)"
    else
        success "Response time acceptable (${time_total}s)"
    fi
}

main() {
    echo "========================================"
    echo "🔒 Heart Portal SSL Testing"
    echo "========================================"
    echo
    
    local all_tests_passed=true
    
    # Test SSL certificate
    if ! test_ssl_certificate; then
        all_tests_passed=false
    fi
    echo
    
    # Test SSL connections
    log "Testing SSL connections..."
    if ! test_ssl_connection "$DOMAIN"; then
        all_tests_passed=false
    fi
    echo
    
    # Test HTTP to HTTPS redirects
    if ! test_http_redirect "$DOMAIN"; then
        all_tests_passed=false
    fi
    if ! test_http_redirect "$WWW_DOMAIN"; then
        all_tests_passed=false
    fi
    echo
    
    # Test all HTTPS endpoints
    log "Testing HTTPS endpoints..."
    test_https_endpoint "https://$DOMAIN/" 200 "Main Portal" || all_tests_passed=false
    test_https_endpoint "https://$DOMAIN/health" 200 "Health Check" || all_tests_passed=false
    test_https_endpoint "https://$DOMAIN/nutrition-database/" 200 "Nutrition Database" || all_tests_passed=false
    test_https_endpoint "https://$DOMAIN/food-base/" 200 "Food Base" || all_tests_passed=false
    test_https_endpoint "https://$DOMAIN/blog-manager/" 200 "Blog Manager" || all_tests_passed=false
    echo
    
    # Test www redirect
    test_https_endpoint "https://$WWW_DOMAIN/" 301 "WWW Redirect" || all_tests_passed=false
    echo
    
    # Test security headers
    test_security_headers "https://$DOMAIN/"
    echo
    
    # Test performance
    test_performance "https://$DOMAIN/"
    echo
    
    # Overall result
    if [ "$all_tests_passed" = true ]; then
        success "🎉 All SSL tests passed!"
    else
        error "⚠️  Some SSL tests failed - check configuration"
        exit 1
    fi
}

case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal SSL Testing Script"
        echo
        echo "Usage: ./test-ssl.sh [options]"
        echo
        echo "This script performs comprehensive SSL/HTTPS testing:"
        echo "1. SSL certificate validation"
        echo "2. SSL connection handshake"
        echo "3. HTTP to HTTPS redirects"
        echo "4. HTTPS endpoint availability"
        echo "5. Security headers analysis"
        echo "6. Performance metrics"
        echo
        echo "Run this after SSL setup to verify everything is working."
        echo
        ;;
    *)
        main "$@"
        ;;
esac