#!/bin/bash

# Start all Heart Portal apps locally using virtual environment
# This ensures all apps use venv packages, not system Python

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/mrrobot/VSCodeProjects/Heart-Portal-Main"
VENV_PATH="$PROJECT_ROOT/venv"

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

# Check if we're in the right directory
check_environment() {
    if [ "$(pwd)" != "$PROJECT_ROOT" ]; then
        log "Changing to project directory..."
        cd "$PROJECT_ROOT"
    fi

    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found at $VENV_PATH"
        error "Run: python3 -m venv venv && pip install -r requirements.txt"
        exit 1
    fi

    success "Environment check passed"
}

# Kill existing Flask processes
kill_existing() {
    log "Checking for existing Flask processes..."

    # Get PIDs of running Flask apps
    PIDS=$(lsof -ti :3000,:5000,:5001,:5002,:5003,:5004,:5005 2>/dev/null || true)

    if [ -n "$PIDS" ]; then
        warning "Found running Flask apps on ports 3000, 5000-5005"
        echo "PIDs: $PIDS"
        echo
        read -p "Kill existing processes? (y/n): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for pid in $PIDS; do
                log "  Killing process $pid..."
                kill -9 $pid 2>/dev/null || true
            done
            sleep 2
            success "Stopped existing processes"
        else
            warning "Cannot start new apps while old ones are running on same ports"
            echo "Kill them manually with: kill -9 $PIDS"
            exit 1
        fi
    else
        success "No existing Flask processes found"
    fi
}

# Start an app in background
start_app() {
    local app_dir=$1
    local app_name=$2
    local port=$3
    local script_name=${4:-app.py}

    log "Starting $app_name on port $port..."

    cd "$PROJECT_ROOT/$app_dir"

    # Start with venv Python in background
    "$VENV_PATH/bin/python" "$script_name" > "/tmp/heart-portal-${app_name}.log" 2>&1 &
    local pid=$!

    # Wait a moment and check if it started
    sleep 1
    if ps -p $pid > /dev/null; then
        success "  $app_name started (PID: $pid)"
        echo "     Log: /tmp/heart-portal-${app_name}.log"
        echo "     URL: http://localhost:$port"
    else
        error "  $app_name failed to start"
        echo "     Check log: /tmp/heart-portal-${app_name}.log"
    fi

    cd "$PROJECT_ROOT"
}

# Verify apps are using venv
verify_venv() {
    log "Verifying apps are using virtual environment..."

    sleep 2  # Give apps time to fully start

    # Get one of the PIDs
    local pid=$(lsof -ti :3000 | head -1)

    if [ -n "$pid" ]; then
        local python_path=$(ps -p $pid -o command= | awk '{print $1}')
        if [[ "$python_path" == *"venv"* ]]; then
            success "Apps are using virtual environment ✓"
            echo "   Python: $python_path"
        else
            warning "Apps may not be using venv"
            echo "   Python: $python_path"
        fi
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "🚀 Start Heart Portal Apps (Local Venv)"
    echo "=========================================="
    echo

    check_environment
    kill_existing

    echo
    log "Starting all applications with venv..."
    echo

    # Start each app
    start_app "main-app" "main-app" 3000 "main_app.py"
    start_app "Nutrition-Database" "nutrition-db" 5000
    start_app "Food-Base" "food-base" 5001
    start_app "Blog-Manager" "blog-manager" 5002
    start_app "Sodium-Tracker" "sodium-tracker" 5003
    start_app "Fluid-Tracker" "fluid-tracker" 5004
    start_app "Weight-Tracker" "weight-tracker" 5005
    # start_app "BP-Monitor" "bp-monitor" 5006  # Uncomment if you want BP Monitor

    echo
    verify_venv

    echo
    success "All applications started! 🎉"
    echo
    echo "📱 Access your apps:"
    echo "   🏠 Main App:         http://localhost:3000"
    echo "   🔍 Nutrition DB:     http://localhost:5000"
    echo "   🍎 Food Base:        http://localhost:5001"
    echo "   📝 Blog Manager:     http://localhost:5002"
    echo "   🧂 Sodium Tracker:   http://localhost:5003"
    echo "   💧 Fluid Tracker:    http://localhost:5004"
    echo "   ⚖️  Weight Tracker:   http://localhost:5005"
    echo
    echo "📊 View logs:"
    echo "   tail -f /tmp/heart-portal-*.log"
    echo
    echo "🛑 Stop all apps:"
    echo "   ./scripts/stop-local-venv.sh"
    echo "   (or: pkill -f 'venv.*python.*app.py')"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Start Heart Portal Apps Locally (with Venv)"
        echo
        echo "Usage: ./start-local-venv.sh"
        echo
        echo "This script will:"
        echo "1. Check for existing Flask processes on ports 3000, 5000-5005"
        echo "2. Offer to kill them if found"
        echo "3. Start all apps using venv Python"
        echo "4. Run apps in background with logs to /tmp/"
        echo
        echo "Requirements:"
        echo "  - Virtual environment at ./venv/"
        echo "  - Dependencies installed: pip install -r requirements.txt"
        echo
        ;;
    *)
        main "$@"
        ;;
esac
