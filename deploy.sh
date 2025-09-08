#!/bin/bash

# Heart Portal Local Deployment Script
# Pushes changes to GitHub and triggers server deployment

set -e  # Exit on any error

SERVER_HOST="129.212.181.161"
SSH_KEY="./Food-Base/heart_portal_key"
PROJECT_DIR="/opt/heart-portal"

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

# Check if there are uncommitted changes
check_git_status() {
    log "Checking git status..."
    
    if ! git diff-index --quiet HEAD --; then
        warning "You have uncommitted changes. Please commit them first:"
        git status --porcelain
        echo
        echo "Run: git add . && git commit -m \"Your commit message\""
        return 1
    fi
    
    success "No uncommitted changes found"
}

# Push to GitHub
push_to_github() {
    log "Pushing to GitHub repository..."
    
    # Check if we're ahead of origin
    LOCAL_COMMITS=$(git rev-list HEAD --not --remotes=origin | wc -l)
    if [ "$LOCAL_COMMITS" -eq 0 ]; then
        warning "No new commits to push"
    else
        success "Pushing $LOCAL_COMMITS new commit(s) to GitHub"
        git push origin main
    fi
}

# Deploy to server
deploy_to_server() {
    log "Deploying to Heart Portal server..."
    
    # Check if SSH key exists
    if [ ! -f "$SSH_KEY" ]; then
        error "SSH key not found at $SSH_KEY"
        return 1
    fi
    
    # Execute deployment on server
    ssh -i "$SSH_KEY" root@"$SERVER_HOST" "cd $PROJECT_DIR && ./deploy.sh"
}

# Main deployment process
main() {
    echo "========================================"
    echo "🚀 Heart Portal Deployment"
    echo "========================================"
    echo
    
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
    echo "Your Heart Portal is now live at:"
    echo "🌐 Main Site: https://heartfailureportal.com"
    echo "🔍 API Manager: https://heartfailureportal.com/api-manager/"
    echo "🍎 Food-Base: https://heartfailureportal.com/food-base/"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Deployment Script"
        echo
        echo "Usage: ./deploy.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  (no args)   Deploy to production server"
        echo
        echo "This script will:"
        echo "1. Check for uncommitted changes"
        echo "2. Push commits to GitHub"
        echo "3. Deploy to production server"
        echo "4. Restart all services"
        echo "5. Verify deployment health"
        ;;
    *)
        main "$@"
        ;;
esac