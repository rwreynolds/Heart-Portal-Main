#!/bin/bash

# Heart Portal Rollback Script
# Rolls back production server to previous version
# Can be run locally to rollback remote server or directly on server

set -e

# Server connection details
SERVER_HOST="129.212.181.161"
SERVER_USER="heartportal"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"
PROJECT_DIR="/opt/heart-portal"

# Detect if we're running locally or on the server
if [ "$(whoami)" = "$SERVER_USER" ] && [ "$(hostname -I 2>/dev/null | grep -q "$SERVER_HOST" && echo "server" || echo "local")" = "server" ]; then
    RUN_MODE="server"
else
    RUN_MODE="local"
fi

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

# Execute command locally or remotely
remote_exec() {
    if [ "$RUN_MODE" = "local" ]; then
        ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "$1"
    else
        eval "$1"
    fi
}

# Get current commit on server
get_current_commit() {
    if [ "$RUN_MODE" = "local" ]; then
        ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "cd $PROJECT_DIR && git rev-parse --short HEAD"
    else
        cd "$PROJECT_DIR" && git rev-parse --short HEAD
    fi
}

# Get previous commit on server
get_previous_commit() {
    if [ "$RUN_MODE" = "local" ]; then
        ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "cd $PROJECT_DIR && git rev-parse --short HEAD~1"
    else
        cd "$PROJECT_DIR" && git rev-parse --short HEAD~1
    fi
}

# Get commit info
get_commit_info() {
    local commit_hash=$1
    if [ "$RUN_MODE" = "local" ]; then
        ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "cd $PROJECT_DIR && git show --oneline --no-patch $commit_hash"
    else
        cd "$PROJECT_DIR" && git show --oneline --no-patch "$commit_hash"
    fi
}

# Check if services are healthy before rollback
check_services_health() {
    log "Checking current service health..."

    local failed_services=()
    for service in heart-portal-main heart-portal-nutrition heart-portal-food heart-portal-blog nginx; do
        if ! remote_exec "systemctl is-active --quiet $service" >/dev/null 2>&1; then
            failed_services+=("$service")
        fi
    done

    if [ ${#failed_services[@]} -gt 0 ]; then
        error "The following services are currently not running: ${failed_services[*]}"
        echo "Consider fixing current issues before rollback or use --force to proceed anyway."
        return 1
    fi

    success "All services are currently healthy"
}

# Server-side rollback process
server_rollback() {
    local target_commit=$1
    local force=${2:-false}

    echo "========================================"
    echo "🔄 Server-side Rollback"
    echo "========================================"
    echo

    cd "$PROJECT_DIR"

    # Get current state
    local current_commit=$(git rev-parse --short HEAD)
    log "Current commit: $(git show --oneline --no-patch $current_commit)"
    log "Rolling back to: $(git show --oneline --no-patch $target_commit)"
    echo

    # Create rollback tag for easy recovery
    local rollback_tag="rollback-from-$current_commit-$(date +%Y%m%d-%H%M%S)"
    log "Creating rollback tag: $rollback_tag"
    git tag "$rollback_tag" HEAD

    log "Stopping Heart Portal services..."
    sudo systemctl stop heart-portal-main heart-portal-nutrition heart-portal-food heart-portal-blog || true

    log "Checking out target commit: $target_commit"
    git checkout "$target_commit"

    log "Installing/updating dependencies..."
    cd main-app && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
    cd Nutrition-Database && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
    cd Food-Base && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
    cd Blog-Manager && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..

    log "Starting Heart Portal services..."
    sudo systemctl start heart-portal-main heart-portal-nutrition heart-portal-food heart-portal-blog

    log "Waiting for services to start..."
    sleep 5

    log "Checking service status..."
    local failed_services=()
    for service in heart-portal-main heart-portal-nutrition heart-portal-food heart-portal-blog; do
        if ! sudo systemctl is-active --quiet "$service"; then
            failed_services+=("$service")
        fi
    done

    if [ ${#failed_services[@]} -gt 0 ]; then
        error "Some services failed to start after rollback: ${failed_services[*]}"
        echo
        echo "🚨 ROLLBACK FAILED - attempting to restore previous state..."

        # Attempt to restore
        git checkout "$rollback_tag"
        sudo systemctl start heart-portal-main heart-portal-nutrition heart-portal-food heart-portal-blog
        sleep 5

        echo "Service status after restore attempt:"
        sudo systemctl status heart-portal-* --no-pager || true
        echo
        echo "🔧 Manual recovery may be needed. Check logs:"
        echo "  journalctl -u heart-portal-main -f"
        echo "  systemctl status heart-portal-*"
        return 1
    fi

    success "All services started successfully after rollback!"
    echo
    echo "📋 Rollback Summary:"
    echo "  Previous: $current_commit"
    echo "  Current:  $target_commit"
    echo "  Recovery tag: $rollback_tag (use 'git checkout $rollback_tag' to restore)"
    echo
    success "Server rollback completed! ✅"
}

# Main rollback process (runs locally)
main() {
    local force=false
    local target_commit=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force=true
                shift
                ;;
            --commit)
                target_commit="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    echo "========================================"
    echo "🔄 Heart Portal Rollback"
    if [ "$RUN_MODE" = "local" ]; then
        echo "🌍 Target server: $SERVER_HOST"
    else
        echo "🖥️  Running on server: $(hostname)"
    fi
    echo "========================================"
    echo

    # Get current and previous commits
    local current_commit=$(get_current_commit)
    if [ -z "$target_commit" ]; then
        target_commit=$(get_previous_commit)
    fi

    if [ -z "$current_commit" ] || [ -z "$target_commit" ]; then
        error "Failed to determine commit hashes"
        exit 1
    fi

    # Show rollback plan
    log "Rollback Plan:"
    echo "  Current version: $(get_commit_info $current_commit)"
    echo "  Target version:  $(get_commit_info $target_commit)"
    echo

    # Safety checks (unless forced)
    if [ "$force" != "true" ]; then
        # Check if services are healthy
        if ! check_services_health; then
            echo
            echo "Use --force to rollback anyway, but be aware this may cause additional issues."
            exit 1
        fi

        # Confirmation prompt
        echo
        warning "This will rollback your production server to the previous version!"
        echo "This action will:"
        echo "  • Stop all Heart Portal services"
        echo "  • Checkout the previous commit"
        echo "  • Reinstall dependencies"
        echo "  • Restart all services"
        echo "  • Create a recovery tag for easy restoration"
        echo
        read -p "Are you sure you want to proceed? (yes/no): " -r
        echo
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Rollback cancelled."
            exit 0
        fi
    else
        warning "Force mode enabled - skipping safety checks"
    fi

    # Execute rollback
    if [ "$RUN_MODE" = "local" ]; then
        log "Executing rollback on remote server..."
        ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "cd $PROJECT_DIR && ./scripts/rollback.sh server --target '$target_commit'"
    else
        server_rollback "$target_commit" "$force"
    fi

    echo
    success "Rollback completed! 🎉"
    echo
    echo "Your Heart Portal has been rolled back:"
    echo "🌐 Main Site: https://heartfailureportal.com"
    echo "🔍 Nutrition-DB: https://heartfailureportal.com/nutrition-database/"
    echo "🍎 Food-Base: https://heartfailureportal.com/food-base/"
    echo "📝 Blog: https://heartfailureportal.com/blog-manager/"
    echo
    echo "💡 To restore the previous version, use:"
    echo "   git checkout rollback-from-$current_commit-$(date +%Y%m%d)"
}

# Handle command line arguments
case "${1:-}" in
    "server")
        # Server-side rollback mode (called via SSH)
        shift
        target_commit=""
        while [[ $# -gt 0 ]]; do
            case $1 in
                --target)
                    target_commit="$2"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done
        server_rollback "$target_commit"
        ;;
    "help"|"-h"|"--help")
        echo "Heart Portal Rollback Script"
        echo
        echo "Usage: ./rollback.sh [options]"
        echo
        echo "Options:"
        echo "  --force           Skip safety checks and confirmations"
        echo "  --commit HASH     Rollback to specific commit (default: previous commit)"
        echo "  help              Show this help message"
        echo
        echo "This script will:"
        echo "1. Check current service health (unless --force)"
        echo "2. Create a recovery tag"
        echo "3. Checkout the target commit"
        echo "4. Reinstall dependencies"
        echo "5. Restart all services"
        echo "6. Verify rollback success"
        echo
        echo "Examples:"
        echo "  ./rollback.sh                    # Rollback to previous commit"
        echo "  ./rollback.sh --force            # Force rollback without checks"
        echo "  ./rollback.sh --commit abc123    # Rollback to specific commit"
        ;;
    *)
        main "$@"
        ;;
esac