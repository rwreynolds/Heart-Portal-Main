#!/bin/bash

# Heart Portal Server Virtual Environment Setup Script
# Adds venv to existing production and staging directories
# Run this on the server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Actual server structure
PRODUCTION_DIR="/opt/heart-portal"
STAGING_DIR="/opt/heart-portal-staging"
PYTHON_CMD="python3"

# Function to print colored output
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

# Check if running on server
check_environment() {
    log "Checking environment..."

    if [ ! -d "$PRODUCTION_DIR" ]; then
        error "Production directory not found: $PRODUCTION_DIR"
        exit 1
    fi

    if [ ! -d "$STAGING_DIR" ]; then
        warning "Staging directory not found: $STAGING_DIR"
        warning "Will only setup production venv"
    fi

    local current_user=$(whoami)
    if [ "$current_user" != "heartportal" ] && [ "$current_user" != "root" ]; then
        warning "Not running as heartportal user. Some operations may require sudo."
    fi

    success "Environment check passed"
}

# Check Python and venv availability
check_python() {
    log "Checking Python installation..."

    if ! command -v $PYTHON_CMD &> /dev/null; then
        error "Python 3 not found. Install with: sudo apt install python3 python3-venv python3-pip"
        exit 1
    fi

    local python_version=$($PYTHON_CMD --version)
    log "Found: $python_version"

    # Check if venv module is available
    if ! $PYTHON_CMD -m venv --help &> /dev/null; then
        error "Python venv module not found. Install with: sudo apt install python3-venv"
        exit 1
    fi

    success "Python and venv ready"
}

# Create virtual environment in a directory
create_venv() {
    local target_dir=$1
    local env_name=$2

    log "Creating virtual environment in $target_dir..."

    if [ ! -d "$target_dir" ]; then
        error "Directory not found: $target_dir"
        return 1
    fi

    cd "$target_dir"

    # Check if venv already exists
    if [ -d "venv" ]; then
        warning "Virtual environment already exists in $target_dir"
        read -p "Recreate it? This will delete the existing venv. (y/n): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            log "Keeping existing venv"
            return 0
        fi
    fi

    # Create venv
    $PYTHON_CMD -m venv venv

    success "Virtual environment created in $target_dir"
}

# Install dependencies
install_dependencies() {
    local target_dir=$1
    local env_name=$2

    log "Installing dependencies in $target_dir..."

    cd "$target_dir"

    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        warning "requirements.txt not found in $target_dir"
        warning "Copying from local project or you'll need to create one"
        return 0
    fi

    # Activate venv and install
    source venv/bin/activate

    log "  Upgrading pip..."
    pip install --upgrade pip --quiet

    log "  Installing requirements..."
    pip install -r requirements.txt

    log "  Verifying key packages..."
    pip list | grep -E "(Flask|psycopg2|reportlab|pandas)" || true

    deactivate

    success "Dependencies installed in $target_dir"
}

# Copy requirements.txt from production to staging if needed
sync_requirements() {
    if [ -f "$PRODUCTION_DIR/requirements.txt" ] && [ -d "$STAGING_DIR" ]; then
        if [ ! -f "$STAGING_DIR/requirements.txt" ]; then
            log "Copying requirements.txt to staging..."
            cp "$PRODUCTION_DIR/requirements.txt" "$STAGING_DIR/"
        fi
    fi
}

# Install systemd service files
install_systemd_services() {
    log "Installing systemd service files..."

    if [ "$EUID" -ne 0 ]; then
        warning "Not running as root. Systemd service installation requires sudo."
        warning "Run these commands manually:"
        echo ""
        echo "# Production services:"
        echo "sudo cp $PRODUCTION_DIR/systemd-services/production/*.service /etc/systemd/system/"
        echo ""
        if [ -d "$STAGING_DIR" ]; then
            echo "# Staging services:"
            echo "sudo cp $PRODUCTION_DIR/systemd-services/staging/*.service /etc/systemd/system/"
            echo ""
        fi
        echo "sudo systemctl daemon-reload"
        echo ""
        return
    fi

    # Copy production services
    if [ -d "$PRODUCTION_DIR/systemd-services/production" ]; then
        cp "$PRODUCTION_DIR/systemd-services/production/*.service" /etc/systemd/system/ 2>/dev/null || true
        success "Production service files installed"
    fi

    # Copy staging services
    if [ -d "$PRODUCTION_DIR/systemd-services/staging" ] && [ -d "$STAGING_DIR" ]; then
        cp "$PRODUCTION_DIR/systemd-services/staging/*.service" /etc/systemd/system/ 2>/dev/null || true
        success "Staging service files installed"
    fi

    # Reload systemd
    systemctl daemon-reload

    success "Systemd services installed and reloaded"
}

# Test environment
test_environment() {
    local target_dir=$1
    local env_name=$2

    log "Testing $env_name environment..."

    cd "$target_dir"

    # Quick test that venv works
    if [ ! -f "venv/bin/python" ]; then
        error "Venv Python not found in $target_dir"
        return 1
    fi

    local venv_python_version=$(venv/bin/python --version)
    log "  Venv Python: $venv_python_version"

    success "$env_name environment test passed"
}

# Print next steps
print_next_steps() {
    echo ""
    echo "=========================================="
    echo "✅ Virtual Environment Setup Complete!"
    echo "=========================================="
    echo ""
    echo "📁 Structure:"
    echo "   - $PRODUCTION_DIR/venv/  (production virtual environment)"
    if [ -d "$STAGING_DIR" ]; then
        echo "   - $STAGING_DIR/venv/     (staging virtual environment)"
    fi
    echo ""
    echo "📝 Next steps:"
    echo ""
    echo "1. Update systemd service files to use venv Python:"
    echo "   Edit: /etc/systemd/system/heart-portal-*.service"
    echo "   Change ExecStart to use: $PRODUCTION_DIR/venv/bin/python"
    echo ""
    if [ -d "$STAGING_DIR" ]; then
        echo "   For staging services:"
        echo "   Change ExecStart to use: $STAGING_DIR/venv/bin/python"
        echo ""
    fi
    echo "2. Reload systemd and restart services:"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl restart heart-portal-*"
    echo ""
    echo "3. Verify services are running:"
    echo "   sudo systemctl status heart-portal-*"
    echo ""
    echo "4. Use new deployment script:"
    echo "   ./scripts/deploy-venv.sh              # Deploy to production"
    if [ -d "$STAGING_DIR" ]; then
        echo "   ./scripts/deploy-venv.sh staging      # Deploy to staging"
    fi
    echo ""
}

# Setup production environment
setup_production() {
    echo ""
    log "Setting up PRODUCTION environment..."
    echo ""

    create_venv "$PRODUCTION_DIR" "production"
    install_dependencies "$PRODUCTION_DIR" "production"
    test_environment "$PRODUCTION_DIR" "production"
}

# Setup staging environment
setup_staging() {
    if [ ! -d "$STAGING_DIR" ]; then
        warning "Staging directory not found, skipping"
        return
    fi

    echo ""
    log "Setting up STAGING environment..."
    echo ""

    sync_requirements
    create_venv "$STAGING_DIR" "staging"
    install_dependencies "$STAGING_DIR" "staging"
    test_environment "$STAGING_DIR" "staging"
}

# Main setup process
main() {
    echo "=========================================="
    echo "🚀 Heart Portal Venv Setup"
    echo "=========================================="
    echo ""

    check_environment
    check_python

    # Setup production
    setup_production

    # Setup staging
    setup_staging

    # Install systemd services
    echo ""
    install_systemd_services

    # Print next steps
    print_next_steps
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Virtual Environment Setup Script"
        echo ""
        echo "Usage: ./setup-venv-server.sh [command]"
        echo ""
        echo "Commands:"
        echo "  help              Show this help message"
        echo "  production-only   Setup only production environment"
        echo "  staging-only      Setup only staging environment"
        echo "  (no args)         Setup both production and staging"
        echo ""
        echo "This script will:"
        echo "1. Create virtual environments in existing directories"
        echo "   - $PRODUCTION_DIR/venv/"
        echo "   - $STAGING_DIR/venv/"
        echo "2. Install dependencies from requirements.txt"
        echo "3. Install systemd service files"
        echo ""
        echo "⚠️  This does NOT stop or modify existing services"
        echo "   Services must be manually updated to use venv paths"
        ;;
    "production-only")
        echo "Setting up PRODUCTION environment only..."
        check_environment
        check_python
        setup_production
        success "Production environment ready!"
        ;;
    "staging-only")
        echo "Setting up STAGING environment only..."
        check_environment
        check_python
        setup_staging
        success "Staging environment ready!"
        ;;
    *)
        main "$@"
        ;;
esac
