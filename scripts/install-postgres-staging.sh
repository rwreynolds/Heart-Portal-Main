#!/bin/bash

# Install PostgreSQL on Staging Server
# This script installs PostgreSQL 15 and creates databases for Heart Portal staging environment

set -e  # Exit on any error

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

# PostgreSQL configuration
PG_VERSION="15"
DB_USER="heartportal"
DB_PASSWORD="${POSTGRES_PASSWORD:-HE080725rwr!}"  # Can override with env var

# Database names for staging
DATABASES=(
    "heart_portal_staging_users"
    "heart_portal_staging_blog"
    "heart_portal_staging_food"
    "heart_portal_staging_sodium"
    "heart_portal_staging_fluid"
    "heart_portal_staging_weight"
    "heart_portal_staging_bp"
)

echo "========================================"
echo "🐘 PostgreSQL Installation for Staging"
echo "========================================"
echo

# Check if running on server
check_environment() {
    log "Checking environment..."

    local hostname=$(hostname)
    if [[ "$hostname" != *"ubuntu"* ]] && [[ "$hostname" != *"heartfailure"* ]]; then
        error "This script must be run ON THE SERVER, not locally!"
        echo "Run this script after SSH'ing to the server:"
        echo "  ssh -i ~/.ssh/id_ed25519 heartportal@129.212.181.161"
        echo "  sudo ./scripts/install-postgres-staging.sh"
        exit 1
    fi

    success "Running on server"
}

# Check if running as root or with sudo
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run with sudo"
        echo "Run: sudo ./scripts/install-postgres-staging.sh"
        exit 1
    fi
    success "Running with sudo privileges"
}

# Install PostgreSQL
install_postgresql() {
    log "Installing PostgreSQL $PG_VERSION..."

    # Check if already installed
    if command -v psql &> /dev/null; then
        local installed_version=$(psql --version | grep -oP '\d+' | head -1)
        warning "PostgreSQL is already installed (version $installed_version)"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi

    # Update package list
    log "Updating package list..."
    apt update -qq

    # Install PostgreSQL
    log "Installing PostgreSQL packages..."
    apt install -y postgresql postgresql-contrib

    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql

    success "PostgreSQL installed and running"
}

# Configure PostgreSQL
configure_postgresql() {
    log "Configuring PostgreSQL..."

    # Allow local connections (already default in Ubuntu)
    # But verify pg_hba.conf allows local Unix socket connections

    # Restart to apply any config changes
    systemctl restart postgresql

    success "PostgreSQL configured"
}

# Create database user
create_db_user() {
    log "Creating database user: $DB_USER..."

    # Check if user already exists
    if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        warning "User $DB_USER already exists"
        read -p "Reset password? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
            success "Password updated"
        fi
    else
        # Create user with password
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
        success "User $DB_USER created"
    fi

    # Grant necessary privileges
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
    success "User privileges granted"
}

# Create databases
create_databases() {
    log "Creating staging databases..."

    for db in "${DATABASES[@]}"; do
        # Check if database exists
        if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$db"; then
            warning "Database $db already exists - skipping"
        else
            # Create database owned by heartportal user
            sudo -u postgres createdb -O "$DB_USER" "$db"
            success "Created database: $db"
        fi
    done

    echo
    success "All databases created"
}

# Test database connections
test_connections() {
    log "Testing database connections..."

    all_good=true
    for db in "${DATABASES[@]}"; do
        if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$db" -c "SELECT 1;" > /dev/null 2>&1; then
            success "  ✓ $db - connection successful"
        else
            error "  ✗ $db - connection failed"
            all_good=false
        fi
    done

    echo
    if [ "$all_good" = true ]; then
        success "All database connections working!"
    else
        error "Some database connections failed"
        exit 1
    fi
}

# Save connection details
save_connection_info() {
    log "Saving connection information..."

    local info_file="/opt/heart-portal-staging/.postgres-connection-info"

    cat > "$info_file" << EOF
# PostgreSQL Connection Information for Staging
# Generated: $(date)

Database User: $DB_USER
Database Password: $DB_PASSWORD

Databases:
EOF

    for db in "${DATABASES[@]}"; do
        echo "  - $db" >> "$info_file"
    done

    cat >> "$info_file" << EOF

Connection String Format:
postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/DATABASE_NAME

Example for users database:
postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/heart_portal_staging_users

Test connection:
PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d heart_portal_staging_users
EOF

    chmod 600 "$info_file"
    chown heartportal:heartportal "$info_file"

    success "Connection info saved to: $info_file"
}

# Display summary
display_summary() {
    echo
    echo "========================================"
    echo "✅ PostgreSQL Installation Complete!"
    echo "========================================"
    echo
    echo "📊 Summary:"
    echo "  PostgreSQL Version: $(psql --version | grep -oP '\d+\.\d+')"
    echo "  Database User: $DB_USER"
    echo "  Password: $DB_PASSWORD"
    echo
    echo "📦 Databases Created:"
    for db in "${DATABASES[@]}"; do
        echo "  ✓ $db"
    done
    echo
    echo "🔗 Connection String Template:"
    echo "  postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/DATABASE_NAME"
    echo
    echo "🔍 Test connection:"
    echo "  PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d heart_portal_staging_users"
    echo
    echo "📝 Connection details saved to:"
    echo "  /opt/heart-portal-staging/.postgres-connection-info"
    echo
    echo "⚠️  IMPORTANT SECURITY NOTE:"
    echo "  This password is temporary. Change it for production:"
    echo "  sudo -u postgres psql -c \"ALTER USER $DB_USER WITH PASSWORD 'new_secure_password';\""
    echo
    echo "📋 Next Steps:"
    echo "  1. Update staging .env files with database connection strings"
    echo "  2. Run database migration scripts to import SQLite data"
    echo "  3. Update application code to use PostgreSQL"
    echo "  4. Test all applications with new database"
    echo
}

# Main installation process
main() {
    check_environment
    check_root

    echo "This script will:"
    echo "  1. Install PostgreSQL $PG_VERSION"
    echo "  2. Create database user: $DB_USER"
    echo "  3. Create ${#DATABASES[@]} staging databases"
    echo "  4. Configure access permissions"
    echo
    echo "Database password: $DB_PASSWORD"
    echo
    read -p "Continue with installation? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 0
    fi

    echo
    install_postgresql
    configure_postgresql
    create_db_user
    create_databases
    test_connections
    save_connection_info
    display_summary
}

# Run main installation
main "$@"
