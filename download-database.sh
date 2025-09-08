#!/bin/bash

# Heart Portal Database Download Script
# Downloads the production database to local development environment

set -e  # Exit on any error

SERVER_HOST="129.212.181.161"
SSH_KEY="./Food-Base/heart_portal_key"
SERVER_DB_PATH="/opt/heart-portal/Food-Base/database/food_base.db"
LOCAL_DB_PATH="./Food-Base/database/food_base.db"

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

# Check if SSH key exists
check_ssh_key() {
    if [ ! -f "$SSH_KEY" ]; then
        error "SSH key not found at $SSH_KEY"
        return 1
    fi
}

# Backup local database if it exists
backup_local_database() {
    if [ -f "$LOCAL_DB_PATH" ]; then
        local backup_path="./Food-Base/database/food_base_local_backup_$(date +%Y%m%d_%H%M%S).db"
        log "Backing up local database to $backup_path"
        cp "$LOCAL_DB_PATH" "$backup_path"
        success "Local database backed up"
    else
        log "No existing local database to backup"
    fi
}

# Download database from server
download_database() {
    log "Downloading production database from server..."
    
    # Create local database directory if it doesn't exist
    mkdir -p "./Food-Base/database"
    
    # Download the database file
    scp -i "$SSH_KEY" "root@$SERVER_HOST:$SERVER_DB_PATH" "$LOCAL_DB_PATH"
    
    success "Database downloaded successfully"
}

# Show database info
show_database_info() {
    log "Checking database information..."
    
    # Get server database info
    local server_info=$(ssh -i "$SSH_KEY" root@"$SERVER_HOST" "
        if [ -f '$SERVER_DB_PATH' ]; then
            echo \"Size: \$(du -h '$SERVER_DB_PATH' | cut -f1)\"
            echo \"Modified: \$(date -r '$SERVER_DB_PATH')\"
        else
            echo \"Database not found on server\"
        fi
    ")
    
    # Get local database info
    local local_info=""
    if [ -f "$LOCAL_DB_PATH" ]; then
        local_info="Size: $(du -h "$LOCAL_DB_PATH" | cut -f1)"$'\n'"Modified: $(date -r "$LOCAL_DB_PATH")"
    else
        local_info="Database not found locally"
    fi
    
    echo
    echo "📊 Database Information:"
    echo "========================"
    echo "Server Database:"
    echo "$server_info" | sed 's/^/  /'
    echo
    echo "Local Database:"
    echo "$local_info" | sed 's/^/  /'
    echo
}

# Count foods in database
count_foods() {
    if [ -f "$LOCAL_DB_PATH" ]; then
        log "Counting foods in downloaded database..."
        local count=$(sqlite3 "$LOCAL_DB_PATH" "SELECT COUNT(*) FROM foods;" 2>/dev/null || echo "Error reading database")
        success "Local database now contains $count foods"
    fi
}

# Main function
main() {
    echo "========================================"
    echo "📥 Heart Portal Database Download"
    echo "========================================"
    echo
    
    # Check prerequisites
    if ! check_ssh_key; then
        exit 1
    fi
    
    # Show current database info
    show_database_info
    
    # Ask for confirmation
    echo -n "Do you want to download the production database? This will replace your local database. (y/N): "
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            ;;
        *)
            warning "Download cancelled"
            exit 0
            ;;
    esac
    
    echo
    
    # Backup local database
    backup_local_database
    
    # Download from server
    download_database
    
    # Show updated info
    show_database_info
    
    # Count foods
    count_foods
    
    echo
    success "Database download completed! 🎉"
    echo
    echo "Your local Food-Base now has the same data as production."
    echo "Any changes you make locally will NOT affect the production database."
    echo
    warning "Remember: Local database changes are not deployed to production!"
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Database Download Script"
        echo
        echo "Usage: ./download-database.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  (no args)   Download production database to local"
        echo
        echo "This script will:"
        echo "1. Backup your current local database (if exists)"
        echo "2. Download the production database"
        echo "3. Replace your local database"
        echo "4. Show database statistics"
        echo
        echo "Note: This only affects your LOCAL database."
        echo "Local changes are never deployed to production."
        ;;
    *)
        main "$@"
        ;;
esac