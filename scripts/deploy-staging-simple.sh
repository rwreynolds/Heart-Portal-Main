#!/bin/bash

# Heart Portal Staging Simple Deployment Script
# Updates code on staging server while preserving PostgreSQL databases and configuration
# Works with existing Gunicorn + PostgreSQL setup

set -e  # Exit on any error

SERVER_HOST="129.212.181.161"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"
STAGING_DIR="/opt/heart-portal-staging"
BRANCH="${BRANCH:-postgres-migration}"  # Default to postgres-migration branch

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check environment (local machine only)
check_environment() {
    log "Checking development environment..."

    local current_dir=$(pwd)
    local expected_path="/Users/mrrobot/VSCodeProjects/Heart-Portal-Main"

    if [[ "$current_dir" != "$expected_path" ]]; then
        error "Wrong directory! You're in: $current_dir"
        error "Should be in: $expected_path"
        echo "Run: cd $expected_path"
        return 1
    fi

    local hostname=$(hostname)
    if [[ "$hostname" == *"ubuntu"* ]] || [[ "$hostname" == *"heartfailure"* ]]; then
        error "WARNING: You appear to be on the server!"
        error "Never deploy from the server. Work locally instead."
        return 1
    fi

    success "Environment check passed - you're working locally"
}

# Select branch for deployment
select_branch() {
    # If branch already specified via env var, use it
    if [ "$BRANCH" != "postgres-migration" ]; then
        log "Using specified branch: $BRANCH"
        return 0
    fi

    log "Fetching available branches..."
    git fetch --all --quiet

    # Get list of all branches (local and remote)
    branches=($(git branch -a | sed 's/remotes\/origin\///' | sed 's/^[* ]*//' | grep -v 'HEAD' | sort -u))

    echo
    echo "Available branches:"
    echo "─────────────────────────────────────"
    for i in "${!branches[@]}"; do
        current_branch=$(git branch --show-current)
        if [ "${branches[$i]}" == "$current_branch" ]; then
            echo "  $((i+1))) ${branches[$i]} ⭐ (current)"
        else
            echo "  $((i+1))) ${branches[$i]}"
        fi
    done
    echo "─────────────────────────────────────"
    echo

    # Prompt for branch selection
    while true; do
        read -p "Select branch number to deploy to staging (default: postgres-migration): " branch_num

        # Default to postgres-migration if empty
        if [ -z "$branch_num" ]; then
            BRANCH="postgres-migration"
            success "Using default branch: postgres-migration"
            break
        fi

        # Validate input
        if ! [[ "$branch_num" =~ ^[0-9]+$ ]] || [ "$branch_num" -lt 1 ] || [ "$branch_num" -gt "${#branches[@]}" ]; then
            error "Invalid selection. Please enter a number between 1 and ${#branches[@]}"
            continue
        fi

        # Set the selected branch
        BRANCH="${branches[$((branch_num-1))]}"
        success "Selected branch: $BRANCH"
        break
    done
}

# Check for uncommitted changes
check_uncommitted_changes() {
    log "Checking for uncommitted changes..."

    if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
        warning "You have uncommitted changes!"
        echo
        git status --short
        echo
        read -p "Do you want to commit these changes? (y/n): " commit_choice

        if [[ "$commit_choice" =~ ^[Yy]$ ]]; then
            git add -A
            read -p "Enter commit message: " commit_msg
            git commit -m "$commit_msg

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            success "Changes committed"
        else
            warning "Deploying without committing local changes"
            warning "Local uncommitted changes will NOT be deployed"
        fi
    else
        success "No uncommitted changes"
    fi
}

# Push branch to GitHub
push_to_github() {
    log "Pushing $BRANCH to GitHub..."

    # Get current branch
    current_branch=$(git branch --show-current)

    # If deploying a different branch than current, warn
    if [ "$current_branch" != "$BRANCH" ]; then
        warning "Current branch ($current_branch) differs from deploy branch ($BRANCH)"
        warning "Make sure $BRANCH is pushed to GitHub!"
        read -p "Continue with deployment of $BRANCH? (y/n): " continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            error "Deployment cancelled"
            exit 1
        fi
        return 0
    fi

    # Push current branch
    git push origin "$BRANCH"
    success "Pushed $BRANCH to GitHub"
}

# Deploy to staging server
deploy_to_staging() {
    log "Deploying to staging server..."

    if [ ! -f "$SSH_KEY" ]; then
        error "SSH key not found at $SSH_KEY"
        return 1
    fi

    # Execute deployment on server
    ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$SSH_KEY" heartportal@"$SERVER_HOST" << REMOTE_SCRIPT
set -e

echo "========================================"
echo "🔄 Staging Server Deployment"
echo "========================================"

cd "$STAGING_DIR"

# Show current state
echo "Current branch: \$(git branch --show-current)"
echo "Current commit: \$(git log -1 --oneline)"
echo ""

# Stash any local changes (shouldn't be any, but just in case)
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  Stashing local changes on server..."
    git stash
fi

# Fetch latest changes
echo "Fetching latest changes from GitHub..."
git fetch origin "$BRANCH"

# Pull latest code
echo "Pulling latest code from $BRANCH..."
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo ""
echo "Updated to: \$(git log -1 --oneline)"
echo ""

# Check that .env files still exist
echo "Verifying configuration files..."
missing_configs=""
for service in main blog nutrition food sodium fluid weight bp; do
    if [ ! -f "\${service}.env" ]; then
        missing_configs="\$missing_configs \${service}.env"
    fi
done

if [ -n "\$missing_configs" ]; then
    echo "❌ Missing configuration files:\$missing_configs"
    exit 1
fi
echo "✅ All .env files present"
echo ""

# Check PostgreSQL connection
echo "Verifying PostgreSQL..."
if sudo -u postgres psql -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not responding"
    exit 1
fi
echo ""

# Restart all staging services
echo "Restarting staging services..."
sudo systemctl restart heart-portal-staging-main
sudo systemctl restart heart-portal-staging-blog
sudo systemctl restart heart-portal-staging-nutrition
sudo systemctl restart heart-portal-staging-food
sudo systemctl restart heart-portal-staging-sodium
sudo systemctl restart heart-portal-staging-fluid
sudo systemctl restart heart-portal-staging-weight
sudo systemctl restart heart-portal-staging-bp
echo "✅ All services restarted"
echo ""

# Wait for services to initialize
sleep 3

# Check service status
echo "Checking service health..."
failed_services=""
for service in main blog nutrition food sodium fluid weight bp; do
    if systemctl is-active --quiet heart-portal-staging-\$service; then
        echo "✅ heart-portal-staging-\$service: active"
    else
        echo "❌ heart-portal-staging-\$service: FAILED"
        failed_services="\$failed_services heart-portal-staging-\$service"
    fi
done

if [ -n "\$failed_services" ]; then
    echo ""
    echo "❌ Some services failed to start:\$failed_services"
    echo ""
    echo "Checking logs for failed services:"
    for service in \$failed_services; do
        echo "--- \$service (last 10 lines) ---"
        sudo journalctl -u \$service --lines=10 --no-pager
        echo ""
    done
    exit 1
fi

echo ""
echo "========================================"
echo "🎉 Deployment Complete!"
echo "========================================"
echo ""
echo "✅ All staging services running"
echo "🌐 Staging URL: http://heartfailureportal.com:8081"
echo ""

REMOTE_SCRIPT

    if [ $? -eq 0 ]; then
        success "Deployment completed successfully!"
    else
        error "Deployment failed! Check logs above for details."
        return 1
    fi
}

# Main deployment process
main() {
    echo "========================================"
    echo "🚀 Staging Deployment (Simple)"
    echo "========================================"
    echo
    echo "This script will:"
    echo "  1. Push your code to GitHub"
    echo "  2. Pull code on staging server"
    echo "  3. Restart Gunicorn services"
    echo "  4. Verify all services are healthy"
    echo
    echo "⚠️  PRESERVES:"
    echo "  • PostgreSQL databases (no data loss)"
    echo "  • .env configuration files"
    echo "  • gunicorn_config.py files"
    echo
    echo "========================================"
    echo

    # Check environment
    if ! check_environment; then
        exit 1
    fi

    # Select branch
    select_branch

    # Check for uncommitted changes
    check_uncommitted_changes

    # Push to GitHub
    if ! push_to_github; then
        exit 1
    fi

    # Deploy to staging
    if ! deploy_to_staging; then
        exit 1
    fi

    echo
    success "Staging deployment completed! 🎉"
    echo
    echo "📦 Deployed branch: $BRANCH"
    echo "🌐 Staging URL: http://heartfailureportal.com:8081"
    echo
    echo "📊 Monitor services:"
    echo "ssh -i $SSH_KEY heartportal@$SERVER_HOST 'sudo systemctl status heart-portal-staging-*'"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Staging Simple Deployment Script"
        echo
        echo "Usage: ./deploy-staging-simple.sh [options]"
        echo
        echo "Options:"
        echo "  help, -h, --help    Show this help message"
        echo "  (no args)           Deploy to staging (interactive)"
        echo
        echo "Environment Variables:"
        echo "  BRANCH=name         Specify branch to deploy (default: postgres-migration)"
        echo
        echo "Examples:"
        echo "  ./scripts/deploy-staging-simple.sh                    # Interactive"
        echo "  BRANCH=main ./scripts/deploy-staging-simple.sh        # Deploy main"
        echo "  BRANCH=postgres-migration ./scripts/deploy-staging-simple.sh"
        echo
        echo "What this script does:"
        echo "  ✅ Pushes code to GitHub"
        echo "  ✅ Pulls code on staging server"
        echo "  ✅ Restarts Gunicorn services"
        echo "  ✅ Verifies service health"
        echo
        echo "What this script PRESERVES:"
        echo "  ✅ PostgreSQL databases (no data changes)"
        echo "  ✅ .env configuration files"
        echo "  ✅ gunicorn_config.py files"
        echo
        ;;
    *)
        main "$@"
        ;;
esac
