#!/bin/bash

# Heart Portal Staging Cleanup Script
# Removes staging environment from production server

set -e

SERVER_HOST="129.212.181.161"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"

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

cleanup_staging() {
    log "Cleaning up staging environment on server..."

    if [ ! -f "$SSH_KEY" ]; then
        error "SSH key not found at $SSH_KEY"
        return 1
    fi

    # Create cleanup script
    local cleanup_script=$(cat << 'CLEANUP_END'
#!/bin/bash
set -e

echo "========================================"
echo "🧹 Staging Environment Cleanup"
echo "========================================"

# Stop and disable staging services
echo "Stopping staging services..."
for service in main nutrition food blog sodium fluid weight; do
    if sudo systemctl is-active --quiet heart-portal-staging-$service 2>/dev/null; then
        sudo systemctl stop heart-portal-staging-$service
        echo "✅ Stopped heart-portal-staging-$service"
    fi

    if sudo systemctl is-enabled --quiet heart-portal-staging-$service 2>/dev/null; then
        sudo systemctl disable heart-portal-staging-$service
        echo "✅ Disabled heart-portal-staging-$service"
    fi
done

# Remove systemd service files
echo "Removing systemd service files..."
for service in main nutrition food blog sodium fluid weight; do
    service_file="/etc/systemd/system/heart-portal-staging-$service.service"
    if [ -f "$service_file" ]; then
        sudo rm "$service_file"
        echo "✅ Removed $service_file"
    fi
done

# Reload systemd
sudo systemctl daemon-reload
echo "✅ Reloaded systemd"

# Remove nginx staging configuration
echo "Removing nginx staging configuration..."
if [ -L "/etc/nginx/sites-enabled/heart-portal-staging" ]; then
    sudo rm /etc/nginx/sites-enabled/heart-portal-staging
    echo "✅ Removed nginx sites-enabled link"
fi

if [ -f "/etc/nginx/sites-available/heart-portal-staging" ]; then
    sudo rm /etc/nginx/sites-available/heart-portal-staging
    echo "✅ Removed nginx sites-available config"
fi

# Test nginx configuration and reload
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx configuration reloaded"
else
    echo "❌ Nginx configuration test failed - manual intervention needed"
fi

# Remove staging directory
staging_dir="/opt/heart-portal-staging"
if [ -d "$staging_dir" ]; then
    echo "Removing staging directory: $staging_dir"
    sudo rm -rf "$staging_dir"
    echo "✅ Removed staging directory"
else
    echo "ℹ️  Staging directory not found (already clean)"
fi

echo ""
echo "========================================"
echo "🎉 Staging Cleanup Complete!"
echo "========================================"
echo ""
echo "Production site continues running normally:"
echo "🌐 https://heartfailureportal.com"
echo ""
echo "Port 8081 is now free and staging services are removed."
echo ""
CLEANUP_END
)

    # Execute cleanup on server
    echo "$cleanup_script" | ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$SSH_KEY" heartportal@"$SERVER_HOST" 'cat > /tmp/staging_cleanup.sh && chmod +x /tmp/staging_cleanup.sh && /tmp/staging_cleanup.sh && rm /tmp/staging_cleanup.sh'
}

main() {
    echo "========================================"
    echo "🧹 Heart Portal Staging Cleanup"
    echo "========================================"
    echo

    warning "This will completely remove the staging environment!"
    echo "- Stop all staging services"
    echo "- Remove staging directory (/opt/heart-portal-staging)"
    echo "- Remove nginx staging configuration"
    echo "- Free port 8081"
    echo
    echo "Production site will be unaffected."
    echo

    read -p "Are you sure you want to proceed? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled."
        exit 0
    fi

    cleanup_staging

    echo
    success "Staging cleanup completed! 🎉"
    echo
    echo "The staging environment has been completely removed."
    echo "Production site continues running normally at https://heartfailureportal.com"
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Staging Cleanup Script"
        echo
        echo "Usage: ./cleanup-staging.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  (no args)   Remove staging environment"
        echo
        echo "This script will:"
        echo "1. Stop all staging services"
        echo "2. Remove staging systemd services"
        echo "3. Remove nginx staging configuration"
        echo "4. Delete staging directory"
        echo "5. Free port 8081"
        echo
        echo "Production site will be unaffected."
        ;;
    *)
        main "$@"
        ;;
esac