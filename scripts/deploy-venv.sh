#!/bin/bash

# Heart Portal Deployment Script (Venv-Aware)
# Pushes changes to GitHub and deploys to server with virtual environment support

set -e  # Exit on any error

SERVER_HOST="129.212.181.161"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"
PROJECT_DIR="/opt/heart-portal"
DEPLOY_TARGET="${DEPLOY_TARGET:-production}"  # production or staging
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"  # Git branch to deploy

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check development environment
check_environment() {
    log "Checking development environment..."

    # Check if we're in the correct directory
    local current_dir=$(pwd)
    local expected_path="/Users/mrrobot/VSCodeProjects/Heart-Portal-Main"

    if [[ "$current_dir" != "$expected_path" ]]; then
        error "Wrong directory! You're in: $current_dir"
        error "Should be in: $expected_path"
        echo "Run: cd $expected_path"
        return 1
    fi

    # Check that we're not on the server
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
    # Only prompt for staging deployments
    if [ "$DEPLOY_TARGET" != "staging" ]; then
        DEPLOY_BRANCH="main"
        return 0
    fi

    # If branch already specified via env var, use it
    if [ "$DEPLOY_BRANCH" != "main" ]; then
        log "Using specified branch: $DEPLOY_BRANCH"
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
        read -p "Select branch number to deploy to staging (default: main): " branch_num

        # Default to main if empty
        if [ -z "$branch_num" ]; then
            DEPLOY_BRANCH="main"
            success "Using default branch: main"
            break
        fi

        # Validate input
        if ! [[ "$branch_num" =~ ^[0-9]+$ ]] || [ "$branch_num" -lt 1 ] || [ "$branch_num" -gt "${#branches[@]}" ]; then
            error "Invalid selection. Please enter a number between 1 and ${#branches[@]}"
            continue
        fi

        # Set the selected branch
        DEPLOY_BRANCH="${branches[$((branch_num-1))]}"
        success "Selected branch: $DEPLOY_BRANCH"
        break
    done
}

# Check if there are uncommitted changes and handle auto-commit
check_git_status() {
    log "Checking git status..."

    if ! git diff-index --quiet HEAD --; then
        warning "You have uncommitted changes:"
        git status --porcelain
        echo

        # Prompt for auto-commit
        read -p "Would you like to commit these changes now? (y/n): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo
            read -p "Enter commit message: " commit_message

            if [ -z "$commit_message" ]; then
                error "Commit message cannot be empty"
                return 1
            fi

            log "Adding and committing changes..."
            git add .
            git commit -m "$commit_message"
            success "Changes committed successfully"
        else
            echo
            echo "Please commit your changes manually before deploying:"
            echo "Run: git add . && git commit -m \"Your commit message\""
            return 1
        fi
    else
        success "No uncommitted changes found"
    fi
}

# Push to GitHub
push_to_github() {
    log "Pushing to GitHub repository (branch: $DEPLOY_BRANCH)..."

    # Get current branch
    current_branch=$(git branch --show-current)

    # If deploying a different branch than current, warn user
    if [ "$current_branch" != "$DEPLOY_BRANCH" ]; then
        warning "Current branch ($current_branch) differs from deploy branch ($DEPLOY_BRANCH)"
        warning "Will push $DEPLOY_BRANCH as-is from remote"
        return 0
    fi

    # Check if we're ahead of origin
    LOCAL_COMMITS=$(git rev-list HEAD --not --remotes=origin | wc -l)
    if [ "$LOCAL_COMMITS" -eq 0 ]; then
        warning "No new commits to push"
    else
        success "Pushing $LOCAL_COMMITS new commit(s) to GitHub"
        git push origin "$DEPLOY_BRANCH"
    fi
}

# Deploy to server
deploy_to_server() {
    log "Deploying to Heart Portal server ($DEPLOY_TARGET environment)..."

    # Check if SSH key exists
    if [ ! -f "$SSH_KEY" ]; then
        error "SSH key not found at $SSH_KEY"
        return 1
    fi

    # Execute deployment on server
    ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$SSH_KEY" heartportal@"$SERVER_HOST" \
        "cd /opt/heart-portal && DEPLOY_TARGET=$DEPLOY_TARGET DEPLOY_BRANCH=$DEPLOY_BRANCH ./scripts/deploy-venv.sh server"
}

# Server-side deployment process (runs on production server)
server_deploy() {
    echo "========================================"
    echo "🔄 Server-side Deployment ($DEPLOY_TARGET)"
    echo "========================================"
    echo

    log "Pulling latest changes from GitHub (branch: $DEPLOY_BRANCH)..."
    cd /opt/heart-portal

    # Fetch all branches
    git fetch --all

    # Checkout and pull the specified branch
    git checkout "$DEPLOY_BRANCH"
    git pull origin "$DEPLOY_BRANCH"

    # Determine target directory based on actual server structure
    if [ "$DEPLOY_TARGET" == "staging" ]; then
        TARGET_DIR="/opt/heart-portal-staging"
    else
        TARGET_DIR="/opt/heart-portal"
    fi

    if [ ! -d "$TARGET_DIR" ]; then
        error "Target directory $TARGET_DIR does not exist!"
        error "Run setup-venv-server.sh first to create the venv structure"
        exit 1
    fi

    log "Deploying to $TARGET_DIR..."

    # Copy updated applications
    log "Copying application files..."
    apps=(
        "main-app"
        "Blog-Manager"
        "Nutrition-Database"
        "Food-Base"
        "Sodium-Tracker"
        "Fluid-Tracker"
        "Weight-Tracker"
        "BP-Monitor"
        "shared"
        "scripts"
    )

    for app in "${apps[@]}"; do
        if [ -d "$app" ]; then
            log "  Updating $app..."
            # Use rsync to preserve database files
            rsync -a --exclude='database/*.db' --exclude='*.pyc' --exclude='__pycache__' \
                "$app/" "$TARGET_DIR/$app/"
        fi
    done

    # Copy systemd service files if they exist
    if [ -d "systemd-services/$DEPLOY_TARGET" ]; then
        log "Updating systemd service files..."
        sudo cp systemd-services/$DEPLOY_TARGET/*.service /etc/systemd/system/
        sudo systemctl daemon-reload
    fi

    # Update requirements if changed
    if [ -f "requirements.txt" ]; then
        if ! cmp -s requirements.txt "$TARGET_DIR/requirements.txt"; then
            log "Requirements changed, updating dependencies..."
            cp requirements.txt "$TARGET_DIR/"
            cd "$TARGET_DIR"
            source venv/bin/activate
            pip install -r requirements.txt --quiet
            deactivate
            cd /opt/heart-portal
        else
            log "Requirements unchanged, skipping dependency update"
        fi
    fi

    # Determine which services to restart
    if [ "$DEPLOY_TARGET" == "production" ]; then
        SERVICES=(
            "heart-portal-main"
            "heart-portal-nutrition"
            "heart-portal-food"
            "heart-portal-blog"
            "heart-portal-sodium"
            "heart-portal-fluid"
            "heart-portal-weight"
            "heart-portal-bp"
        )
    else
        SERVICES=(
            "heart-portal-staging-main"
            "heart-portal-staging-nutrition"
            "heart-portal-staging-food"
            "heart-portal-staging-blog"
            "heart-portal-staging-sodium"
            "heart-portal-staging-fluid"
            "heart-portal-staging-weight"
            "heart-portal-staging-bp"
        )
    fi

    log "Restarting services..."
    for service in "${SERVICES[@]}"; do
        log "  Restarting $service..."
        sudo systemctl restart "$service" || warning "Failed to restart $service"
    done

    log "Waiting for services to start..."
    sleep 5

    log "Checking service status..."
    all_good=true
    for service in "${SERVICES[@]}"; do
        if sudo systemctl is-active --quiet "$service"; then
            success "  $service is running"
        else
            error "  $service failed to start"
            all_good=false
        fi
    done

    if [ "$all_good" = true ]; then
        success "Server deployment completed! ✅"
    else
        error "Some services failed to start. Check logs with:"
        echo "  sudo journalctl -u heart-portal-* -n 100"
        return 1
    fi
}

# Main deployment process (runs locally)
main() {
    echo "========================================"
    echo "🚀 Heart Portal Deployment"
    echo "   Target: $DEPLOY_TARGET"
    echo "========================================"
    echo

    # Check development environment
    if ! check_environment; then
        exit 1
    fi

    # Select branch (for staging deployments)
    select_branch

    # Check git status
    if ! check_git_status; then
        exit 1
    fi

    # Push to GitHub
    push_to_github

    # Deploy to server
    deploy_to_server

    echo
    success "Deployment completed! 🎉"
    echo

    if [ "$DEPLOY_TARGET" == "production" ]; then
        echo "Your Heart Portal is now live at:"
        echo "🌐 Main Site: https://heartfailureportal.com"
        echo "🔍 Nutrition-DB: https://heartfailureportal.com/nutrition-database/"
        echo "🍎 Food-Base: https://heartfailureportal.com/food-base/"
        echo "📝 Blog: https://heartfailureportal.com/blog-manager/"
    else
        echo "Your staging environment is updated:"
        echo "🧪 Staging accessible on server ports 3100, 5100-5106"
    fi
    echo
}

# Handle command line arguments
case "${1:-}" in
    "server")
        # Server-side deployment mode (called via SSH)
        server_deploy
        ;;
    "staging")
        # Deploy to staging environment
        DEPLOY_TARGET="staging"
        main "$@"
        ;;
    "production")
        # Deploy to production environment (explicit)
        DEPLOY_TARGET="production"
        main "$@"
        ;;
    "help"|"-h"|"--help")
        echo "Heart Portal Deployment Script (Venv-Aware)"
        echo
        echo "Usage: ./deploy-venv.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  production  Deploy to production (default)"
        echo "  staging     Deploy to staging environment"
        echo "  server      Server-side deployment (internal use)"
        echo
        echo "Environment Variables:"
        echo "  DEPLOY_TARGET=production  Deploy to production (default)"
        echo "  DEPLOY_TARGET=staging     Deploy to staging"
        echo
        echo "Examples:"
        echo "  ./deploy-venv.sh                    # Deploy to production"
        echo "  ./deploy-venv.sh staging            # Deploy to staging"
        echo "  DEPLOY_TARGET=staging ./deploy-venv.sh  # Deploy to staging"
        echo
        echo "This script will:"
        echo "1. Check for uncommitted changes"
        echo "2. Push commits to GitHub"
        echo "3. Deploy to target environment (production or staging)"
        echo "4. Update dependencies in virtual environment"
        echo "5. Restart appropriate services"
        echo "6. Verify deployment health"
        ;;
    *)
        main "$@"
        ;;
esac
