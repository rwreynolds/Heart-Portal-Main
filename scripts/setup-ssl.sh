#!/bin/bash

# Heart Portal SSL Setup Script
# Sets up Nginx with Let's Encrypt SSL certificates

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

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
PROJECT_DIR="/opt/heart-portal"
DOMAIN="heartfailureportal.com"
WWW_DOMAIN="www.heartfailureportal.com"
EMAIL="admin@heartfailureportal.com"  # Change this to your email

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        echo "Run with: sudo ./setup-ssl.sh"
        exit 1
    fi
    
    # Check if we're on the correct server
    if [ ! -d "$PROJECT_DIR" ]; then
        error "Project directory $PROJECT_DIR not found"
        error "This script must be run on the production server"
        exit 1
    fi
    
    # Check if Heart Portal services are running
    local services=("heart-portal-main" "heart-portal-nutrition" "heart-portal-food" "heart-portal-blog")
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet "$service.service"; then
            error "$service is not running"
            echo "Please start Heart Portal services first: systemctl start $service"
            exit 1
        fi
    done
    
    success "Prerequisites checked"
}

install_nginx_certbot() {
    log "Installing Nginx and Certbot..."
    
    # Update package list
    apt update
    
    # Install Nginx
    if ! command -v nginx &> /dev/null; then
        apt install -y nginx
        success "Nginx installed"
    else
        log "Nginx already installed"
    fi
    
    # Install Certbot
    if ! command -v certbot &> /dev/null; then
        apt install -y certbot python3-certbot-nginx
        success "Certbot installed"
    else
        log "Certbot already installed"
    fi
    
    # Remove default Nginx site
    if [ -f "/etc/nginx/sites-enabled/default" ]; then
        rm /etc/nginx/sites-enabled/default
        success "Removed default Nginx site"
    fi
}

configure_nginx() {
    log "Configuring Nginx for Heart Portal..."
    
    # Copy our configuration
    cp "$PROJECT_DIR/nginx/heart-portal.conf" /etc/nginx/sites-available/heart-portal
    
    # Enable the site
    if [ ! -L "/etc/nginx/sites-enabled/heart-portal" ]; then
        ln -s /etc/nginx/sites-available/heart-portal /etc/nginx/sites-enabled/heart-portal
        success "Heart Portal site enabled"
    fi
    
    # Test Nginx configuration
    if nginx -t; then
        success "Nginx configuration is valid"
    else
        error "Nginx configuration is invalid"
        exit 1
    fi
    
    # Start and enable Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    success "Nginx configured and started"
}

obtain_ssl_certificate() {
    log "Obtaining SSL certificate from Let's Encrypt..."
    
    # Stop nginx temporarily if needed for standalone mode
    # systemctl stop nginx
    
    # Get certificate using nginx plugin (recommended)
    certbot --nginx \
        -d "$DOMAIN" \
        -d "$WWW_DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --redirect \
        --non-interactive
    
    if [ $? -eq 0 ]; then
        success "SSL certificate obtained successfully"
    else
        error "Failed to obtain SSL certificate"
        exit 1
    fi
}

configure_auto_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Test certificate renewal
    if certbot renew --dry-run; then
        success "Certificate renewal test successful"
    else
        warning "Certificate renewal test failed - check configuration"
    fi
    
    # Create renewal script
    cat > /etc/cron.d/certbot-renewal << EOF
# Renew Let's Encrypt certificates twice daily
0 */12 * * * root /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
    
    success "Auto-renewal configured (runs twice daily)"
}

configure_firewall() {
    log "Configuring firewall for HTTPS..."
    
    if command -v ufw &> /dev/null; then
        # Allow HTTP and HTTPS
        ufw allow 'Nginx Full'
        ufw --force enable
        success "UFW firewall configured"
    elif command -v iptables &> /dev/null; then
        # Basic iptables rules
        iptables -I INPUT -p tcp --dport 80 -j ACCEPT
        iptables -I INPUT -p tcp --dport 443 -j ACCEPT
        
        # Save rules (depends on distribution)
        if command -v iptables-save &> /dev/null; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        success "Iptables configured"
    else
        warning "No firewall detected - ensure ports 80 and 443 are open"
    fi
}

verify_ssl_setup() {
    log "Verifying SSL setup..."
    
    # Check certificate status
    certbot certificates
    
    # Check Nginx status
    if systemctl is-active --quiet nginx; then
        success "Nginx is running"
    else
        error "Nginx is not running"
        systemctl status nginx --no-pager
    fi
    
    # Test HTTPS connectivity
    log "Testing HTTPS connectivity..."
    sleep 5  # Give services time to restart
    
    if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" | grep -q "200"; then
        success "HTTPS is working correctly"
    else
        warning "HTTPS test failed - check configuration"
    fi
    
    # Show certificate expiration
    local cert_expire=$(openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -dates | grep notAfter | cut -d= -f2)
    log "Certificate expires: $cert_expire"
}

main() {
    echo "========================================"
    echo "🔒 Heart Portal SSL Setup"
    echo "========================================"
    echo
    
    echo "This script will:"
    echo "1. Install Nginx and Certbot"
    echo "2. Configure Nginx as reverse proxy"
    echo "3. Obtain SSL certificates from Let's Encrypt"
    echo "4. Set up automatic renewal"
    echo "5. Configure firewall"
    echo
    
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled"
        exit 0
    fi
    
    echo
    
    # Main setup steps
    check_prerequisites
    echo
    
    install_nginx_certbot
    echo
    
    configure_nginx
    echo
    
    obtain_ssl_certificate
    echo
    
    configure_auto_renewal
    echo
    
    configure_firewall
    echo
    
    verify_ssl_setup
    echo
    
    success "🎉 SSL setup completed successfully!"
    echo
    echo "🔒 Your Heart Portal is now secured with HTTPS:"
    echo "  Main Site:      https://heartfailureportal.com"
    echo "  Nutrition-DB:   https://heartfailureportal.com/nutrition-database/"
    echo "  Food-Base:      https://heartfailureportal.com/food-base/"
    echo "  Blog-Manager:   https://heartfailureportal.com/blog-manager/"
    echo
    echo "📋 SSL management commands:"
    echo "  certbot certificates                 # View certificates"
    echo "  certbot renew                       # Manual renewal"
    echo "  systemctl status nginx              # Check Nginx status"
    echo "  tail -f /var/log/nginx/error.log    # View Nginx errors"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal SSL Setup Script"
        echo
        echo "Usage: sudo ./setup-ssl.sh"
        echo
        echo "This script configures SSL certificates for Heart Portal using Let's Encrypt."
        echo "It sets up Nginx as a reverse proxy and obtains free SSL certificates."
        echo
        echo "Prerequisites:"
        echo "- Heart Portal services must be running"
        echo "- Domain must be pointing to this server"
        echo "- Ports 80 and 443 must be accessible"
        echo
        ;;
    *)
        main "$@"
        ;;
esac