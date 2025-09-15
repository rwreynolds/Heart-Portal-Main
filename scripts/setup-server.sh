#!/bin/bash

# Heart Portal Server Setup Script
# Sets up systemd services, virtual environments, and proper permissions

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

# Server configuration variables
PROJECT_DIR="/opt/heart-portal"
SERVICE_USER="heartportal"
SERVICE_GROUP="heartportal"
PYTHON_VERSION="python3"

# Components to set up
COMPONENTS=("main-app" "Nutrition-Database" "Food-Base" "Blog-Manager")

setup_virtual_environments() {
    log "Setting up virtual environments for all components..."
    
    for component in "${COMPONENTS[@]}"; do
        local comp_dir="$PROJECT_DIR/$component"
        local venv_dir="$comp_dir/venv"
        
        log "Setting up virtual environment for $component..."
        
        if [ ! -d "$comp_dir" ]; then
            error "Component directory $comp_dir does not exist"
            continue
        fi
        
        cd "$comp_dir"
        
        # Create virtual environment if it doesn't exist
        if [ ! -d "$venv_dir" ]; then
            $PYTHON_VERSION -m venv venv
            success "Created virtual environment for $component"
        else
            log "Virtual environment already exists for $component"
        fi
        
        # Activate and install requirements
        source venv/bin/activate
        
        # Upgrade pip
        pip install --upgrade pip
        
        # Install requirements
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
            success "Installed requirements for $component"
        else
            # Fallback to base requirements
            pip install -r ../requirements-base.txt
            success "Installed base requirements for $component"
        fi
        
        deactivate
    done
}

setup_permissions() {
    log "Setting up proper file permissions..."
    
    # Ensure heartportal user owns the project directory
    chown -R $SERVICE_USER:$SERVICE_GROUP $PROJECT_DIR
    
    # Set proper permissions
    find $PROJECT_DIR -type d -exec chmod 755 {} \;
    find $PROJECT_DIR -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    chmod +x $PROJECT_DIR/scripts/*.sh
    
    success "File permissions configured"
}

install_systemd_services() {
    log "Installing systemd service files..."
    
    local service_files=("heart-portal-main.service" "heart-portal-nutrition.service" "heart-portal-food.service" "heart-portal-blog.service")
    
    for service_file in "${service_files[@]}"; do
        local src_file="$PROJECT_DIR/systemd/$service_file"
        local dest_file="/etc/systemd/system/$service_file"
        
        if [ -f "$src_file" ]; then
            cp "$src_file" "$dest_file"
            success "Installed $service_file"
        else
            error "Service file $src_file not found"
        fi
    done
    
    # Reload systemd daemon
    systemctl daemon-reload
    success "Systemd daemon reloaded"
}

enable_and_start_services() {
    log "Enabling and starting Heart Portal services..."
    
    local services=("heart-portal-main" "heart-portal-nutrition" "heart-portal-food" "heart-portal-blog")
    
    for service in "${services[@]}"; do
        log "Enabling $service..."
        systemctl enable "$service.service"
        
        log "Starting $service..."
        systemctl start "$service.service"
        
        # Check if service started successfully
        if systemctl is-active --quiet "$service.service"; then
            success "$service started successfully"
        else
            error "$service failed to start"
            systemctl status "$service.service" --no-pager
        fi
    done
}

verify_setup() {
    log "Verifying server setup..."
    
    # Check all services
    log "Service status:"
    systemctl status heart-portal-* --no-pager
    
    # Check if ports are responding
    local ports=(3000 5000 5001 5002)
    local port_names=("Main-App" "Nutrition-Database" "Food-Base" "Blog-Manager")
    
    log "Checking service ports..."
    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local name=${port_names[$i]}
        
        if ss -tuln | grep -q ":$port "; then
            success "$name (port $port) is listening"
        else
            warning "$name (port $port) is not responding"
        fi
    done
}

main() {
    echo "========================================"
    echo "🚀 Heart Portal Server Setup"
    echo "========================================"
    echo
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        echo "Run with: sudo ./setup-server.sh"
        exit 1
    fi
    
    # Check if we're on the server
    if [ ! -d "$PROJECT_DIR" ]; then
        error "Project directory $PROJECT_DIR not found"
        error "This script must be run on the production server"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    log "Setting up Heart Portal server infrastructure..."
    echo
    
    # Setup steps
    setup_virtual_environments
    echo
    
    setup_permissions
    echo
    
    install_systemd_services
    echo
    
    enable_and_start_services
    echo
    
    verify_setup
    echo
    
    success "🎉 Heart Portal server setup completed!"
    echo
    echo "🌐 Your services should now be running on:"
    echo "  Main Portal:    http://localhost:3000"
    echo "  Nutrition-DB:   http://localhost:5000"
    echo "  Food-Base:      http://localhost:5001"
    echo "  Blog-Manager:   http://localhost:5002"
    echo
    echo "📋 Service management commands:"
    echo "  systemctl status heart-portal-*"
    echo "  systemctl restart heart-portal-main"
    echo "  journalctl -u heart-portal-main -f"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Server Setup Script"
        echo
        echo "Usage: sudo ./setup-server.sh [command]"
        echo
        echo "This script will:"
        echo "1. Create virtual environments for all components"
        echo "2. Install Python dependencies"
        echo "3. Set up proper file permissions"
        echo "4. Install systemd service files"
        echo "5. Enable and start all services"
        echo "6. Verify the setup"
        echo
        echo "Must be run as root on the production server."
        ;;
    *)
        main "$@"
        ;;
esac