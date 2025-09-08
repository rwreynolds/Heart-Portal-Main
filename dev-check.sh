#!/bin/bash

# Heart Portal Development Environment Check
# Verifies you're working in the local project, not on the server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the correct local directory
check_local_directory() {
    local current_dir=$(pwd)
    local expected_path="/Users/mrrobot/VSCodeProjects/Heart-Portal-Main"
    
    if [[ "$current_dir" == "$expected_path" ]]; then
        success "You're in the correct local project directory"
        return 0
    else
        error "Wrong directory! You're in: $current_dir"
        error "Should be in: $expected_path"
        echo
        echo "To fix this, run:"
        echo "cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main"
        return 1
    fi
}

# Check that we're not accidentally SSH'd into the server
check_not_on_server() {
    local hostname=$(hostname)
    
    if [[ "$hostname" == *"ubuntu"* ]] || [[ "$hostname" == *"heartfailure"* ]]; then
        error "⚠️  WARNING: You appear to be on the server!"
        error "Hostname: $hostname"
        echo
        error "You should NOT make changes directly on the server."
        error "Exit this SSH session and work locally instead."
        return 1
    else
        success "You're on your local machine (not the server)"
        info "Hostname: $hostname"
        return 0
    fi
}

# Check if required local files exist
check_local_files() {
    local required_files=(
        ".git"
        "deploy.sh"
        "download-database.sh"
        "DEPLOYMENT.md"
        "API-manager/app.py"
        "Food-Base/app.py"
        "main-app/main_app.py"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ -e "$file" ]]; then
            success "Found: $file"
        else
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        success "All required project files found"
        return 0
    else
        error "Missing files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
}

# Check git status and branch
check_git_status() {
    if [[ ! -d ".git" ]]; then
        error "Not in a git repository"
        return 1
    fi
    
    local branch=$(git branch --show-current)
    local remote_url=$(git remote get-url origin)
    
    success "Git repository detected"
    info "Current branch: $branch"
    info "Remote URL: $remote_url"
    
    if [[ "$remote_url" == *"Heart-Portal-Main"* ]]; then
        success "Correct repository: Heart-Portal-Main"
    else
        warning "Unexpected repository URL: $remote_url"
    fi
    
    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        info "No uncommitted changes"
    else
        warning "You have uncommitted changes:"
        git status --porcelain | sed 's/^/  /'
    fi
}

# Show local development servers
show_local_servers() {
    echo
    echo "🖥️  Local Development Servers:"
    echo "================================"
    echo "Main App:     http://localhost:3000"
    echo "API Manager:  http://localhost:5000"  
    echo "Food-Base:    http://localhost:5001"
    echo
    echo "Production URLs (for reference only):"
    echo "Main Site:    https://heartfailureportal.com"
    echo "API Manager:  https://heartfailureportal.com/api-manager/"
    echo "Food-Base:    https://heartfailureportal.com/food-base/"
}

# Main check function
main() {
    echo "========================================"
    echo "🔍 Heart Portal Development Check"
    echo "========================================"
    echo
    
    local all_good=true
    
    # Run all checks
    if ! check_not_on_server; then
        all_good=false
    fi
    echo
    
    if ! check_local_directory; then
        all_good=false
    fi
    echo
    
    if ! check_local_files; then
        all_good=false
    fi
    echo
    
    if ! check_git_status; then
        all_good=false
    fi
    
    show_local_servers
    
    if $all_good; then
        echo
        success "✨ Environment check passed! You're ready for local development."
        echo
        echo "🚀 Quick Start Commands:"
        echo "  ./deploy.sh           # Deploy your changes"
        echo "  ./download-database.sh # Get production database"
        echo "  ./dev-check.sh        # Run this check anytime"
        echo
        echo "📝 Remember:"
        echo "  - Always work in THIS local directory"
        echo "  - Test locally before deploying"
        echo "  - Never make changes directly on the server"
    else
        echo
        error "❌ Environment check failed. Please fix the issues above."
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Development Environment Check"
        echo
        echo "Usage: ./dev-check.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  (no args)   Run environment check"
        echo
        echo "This script verifies:"
        echo "  - You're in the correct local directory"
        echo "  - You're not accidentally on the server"
        echo "  - All required project files exist"
        echo "  - Git repository is set up correctly"
        echo
        echo "Run this anytime you want to verify your development environment."
        ;;
    *)
        main "$@"
        ;;
esac