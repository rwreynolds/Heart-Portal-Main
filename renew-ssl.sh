#!/bin/bash

# Heart Portal SSL Certificate Renewal Script
# Manual SSL renewal with comprehensive checks

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
LOG_FILE="/var/log/heart-portal-ssl-renewal.log"

log_to_file() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_certificate_expiry() {
    log "Checking certificate expiry..."
    
    if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        error "Certificate not found for $DOMAIN"
        return 1
    fi
    
    local cert_expire=$(openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -dates | grep notAfter | cut -d= -f2)
    local expire_timestamp=$(date -d "$cert_expire" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expire=$(( (expire_timestamp - current_timestamp) / 86400 ))
    
    log "Certificate expires in $days_until_expire days ($cert_expire)"
    log_to_file "Certificate check: $days_until_expire days remaining"
    
    if [ $days_until_expire -le 30 ]; then
        warning "Certificate needs renewal (expires in $days_until_expire days)"
        return 0
    else
        success "Certificate is valid for $days_until_expire days"
        return 1
    fi
}

backup_certificate() {
    log "Creating certificate backup..."
    
    local backup_dir="/opt/heart-portal/ssl-backups"
    local backup_file="$backup_dir/cert-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    mkdir -p "$backup_dir"
    
    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        tar -czf "$backup_file" -C /etc/letsencrypt/live "$DOMAIN"
        success "Certificate backed up to $backup_file"
        log_to_file "Certificate backed up to $backup_file"
    else
        warning "No existing certificate to backup"
        log_to_file "No existing certificate to backup"
    fi
}

renew_certificate() {
    log "Attempting certificate renewal..."
    
    # Test renewal first
    log "Testing renewal process..."
    if certbot renew --dry-run; then
        success "Dry run successful"
        log_to_file "Dry run successful"
    else
        error "Dry run failed"
        log_to_file "Dry run failed"
        return 1
    fi
    
    # Perform actual renewal
    log "Performing certificate renewal..."
    if certbot renew --force-renewal; then
        success "Certificate renewed successfully"
        log_to_file "Certificate renewed successfully"
    else
        error "Certificate renewal failed"
        log_to_file "Certificate renewal failed"
        return 1
    fi
}

reload_services() {
    log "Reloading services..."
    
    # Reload Nginx to use new certificate
    if systemctl reload nginx; then
        success "Nginx reloaded"
        log_to_file "Nginx reloaded successfully"
    else
        error "Failed to reload Nginx"
        log_to_file "Failed to reload Nginx"
        return 1
    fi
    
    # Optionally restart other services if needed
    # systemctl restart heart-portal-*
}

verify_renewal() {
    log "Verifying certificate renewal..."
    
    sleep 5  # Give services time to reload
    
    # Check certificate dates
    local new_cert_expire=$(openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -dates | grep notAfter | cut -d= -f2)
    local new_expire_timestamp=$(date -d "$new_cert_expire" +%s)
    local current_timestamp=$(date +%s)
    local new_days_until_expire=$(( (new_expire_timestamp - current_timestamp) / 86400 ))
    
    if [ $new_days_until_expire -gt 80 ]; then
        success "New certificate valid for $new_days_until_expire days"
        log_to_file "New certificate valid for $new_days_until_expire days"
    else
        error "New certificate may not have been installed correctly"
        log_to_file "New certificate verification failed"
        return 1
    fi
    
    # Test HTTPS connection
    if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" | grep -q "200"; then
        success "HTTPS connection working"
        log_to_file "HTTPS connection verified"
    else
        error "HTTPS connection failed"
        log_to_file "HTTPS connection failed"
        return 1
    fi
}

cleanup_old_backups() {
    log "Cleaning up old certificate backups..."
    
    local backup_dir="/opt/heart-portal/ssl-backups"
    
    if [ -d "$backup_dir" ]; then
        # Keep only last 10 backups
        find "$backup_dir" -name "cert-backup-*.tar.gz" -type f | sort -r | tail -n +11 | xargs -r rm
        local remaining=$(find "$backup_dir" -name "cert-backup-*.tar.gz" -type f | wc -l)
        success "Kept $remaining most recent backups"
        log_to_file "Cleaned up old backups, kept $remaining"
    fi
}

main() {
    echo "========================================"
    echo "🔒 Heart Portal SSL Renewal"
    echo "========================================"
    echo
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        echo "Run with: sudo ./renew-ssl.sh"
        exit 1
    fi
    
    # Create log file
    touch "$LOG_FILE"
    log_to_file "SSL renewal started"
    
    # Check if renewal is needed
    if ! check_certificate_expiry; then
        if [ "${1:-}" != "--force" ]; then
            success "Certificate renewal not needed"
            echo "Use --force to renew anyway"
            exit 0
        else
            warning "Forcing certificate renewal"
        fi
    fi
    
    echo
    
    # Perform renewal steps
    backup_certificate
    echo
    
    renew_certificate
    echo
    
    reload_services
    echo
    
    verify_renewal
    echo
    
    cleanup_old_backups
    echo
    
    success "🎉 SSL certificate renewal completed successfully!"
    log_to_file "SSL renewal completed successfully"
    
    echo
    echo "📋 Certificate status:"
    certbot certificates
    echo
}

case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal SSL Certificate Renewal"
        echo
        echo "Usage: sudo ./renew-ssl.sh [--force]"
        echo
        echo "Options:"
        echo "  --force    Force renewal even if certificate is not due"
        echo "  --help     Show this help message"
        echo
        echo "This script will:"
        echo "1. Check certificate expiry status"
        echo "2. Backup existing certificates"
        echo "3. Renew certificates if needed"
        echo "4. Reload Nginx with new certificates"
        echo "5. Verify the renewal worked"
        echo "6. Clean up old backups"
        echo
        echo "Logs are written to: $LOG_FILE"
        echo
        ;;
    *)
        main "$@"
        ;;
esac