#!/bin/bash

# Heart Portal Staging Deployment Script
# Creates staging environment on production server for testing multiuser-auth branch
# Staging will run on port 8081 with separate services

set -e  # Exit on any error

SERVER_HOST="129.212.181.161"
SSH_KEY="/Users/mrrobot/.ssh/id_ed25519"
STAGING_DIR="/opt/heart-portal-staging"
BRANCH="multiuser-auth"

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

# Check environment (same as production deploy)
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

# Push multiuser-auth branch to GitHub if needed
push_branch_to_github() {
    log "Checking multiuser-auth branch status..."

    # Ensure we're on the multiuser-auth branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$BRANCH" ]; then
        error "You're on branch '$current_branch' but need to be on '$BRANCH'"
        echo "Run: git checkout $BRANCH"
        return 1
    fi

    # Check if branch is pushed
    if git ls-remote --exit-code origin $BRANCH > /dev/null 2>&1; then
        log "Branch $BRANCH exists on origin, checking for new commits..."
        LOCAL_COMMITS=$(git rev-list HEAD --not --remotes=origin/$BRANCH 2>/dev/null | wc -l)
        if [ "$LOCAL_COMMITS" -eq 0 ]; then
            success "Branch is up to date"
        else
            success "Pushing $LOCAL_COMMITS new commit(s) to GitHub"
            git push origin $BRANCH
        fi
    else
        success "Pushing new branch $BRANCH to GitHub"
        git push -u origin $BRANCH
    fi
}

# Deploy staging to server
deploy_staging_to_server() {
    log "Deploying staging environment to server..."

    if [ ! -f "$SSH_KEY" ]; then
        error "SSH key not found at $SSH_KEY"
        return 1
    fi

    # Create the staging deployment script
    local staging_script=$(cat << 'SCRIPT_END'
#!/bin/bash
set -e

STAGING_DIR="/opt/heart-portal-staging"
BRANCH="multiuser-auth"
PRODUCTION_DIR="/opt/heart-portal"

echo "========================================"
echo "🔄 Staging Environment Setup"
echo "========================================"

# Create staging directory if it doesn't exist
if [ ! -d "$STAGING_DIR" ]; then
    echo "Creating staging directory..."
    sudo mkdir -p "$STAGING_DIR"
    sudo chown heartportal:heartportal "$STAGING_DIR"
fi

# Clone or update staging repository
if [ ! -d "$STAGING_DIR/.git" ]; then
    echo "Cloning repository for staging..."
    cd "$STAGING_DIR"
    git clone https://github.com/rwreynolds/Heart-Portal-Main.git .
else
    echo "Updating staging repository..."
    cd "$STAGING_DIR"
    git fetch origin
fi

# Switch to multiuser-auth branch
echo "Switching to multiuser-auth branch..."
git checkout "$BRANCH"
git pull origin "$BRANCH"

# Copy environment configuration from production
echo "Setting up staging environment..."
if [ -f "$PRODUCTION_DIR/.env" ]; then
    cp "$PRODUCTION_DIR/.env" "$STAGING_DIR/.env"

    # Override staging-specific settings
    sed -i 's/STAGING_MODE=false/STAGING_MODE=true/' "$STAGING_DIR/.env"
    echo "✅ Copied .env from production and configured for staging"
fi

# Create staging systemd services
echo "Creating staging systemd services..."

# Main service
sudo tee /etc/systemd/system/heart-portal-staging-main.service > /dev/null << 'SERVICE_MAIN'
[Unit]
Description=Heart Portal Staging Main Application
After=network.target

[Service]
Type=simple
User=heartportal
WorkingDirectory=/opt/heart-portal-staging/main-app
Environment=PATH=/opt/heart-portal-staging/main-app/venv/bin
ExecStart=/opt/heart-portal-staging/main-app/venv/bin/python main_app.py
Restart=always
RestartSec=10
Environment=FLASK_ENV=staging
Environment=PORT=3001
Environment=STAGING_MODE=true

[Install]
WantedBy=multi-user.target
SERVICE_MAIN

# Other services
declare -A SERVICES
SERVICES[nutrition]="Nutrition-Database:5006"
SERVICES[food]="Food-Base:5007"
SERVICES[blog]="Blog-Manager:5008"
SERVICES[sodium]="Sodium-Tracker:5009"
SERVICES[fluid]="Fluid-Tracker:5010"
SERVICES[weight]="Weight-Tracker:5011"

for service in "${!SERVICES[@]}"; do
    IFS=':' read -r dir port <<< "${SERVICES[$service]}"

sudo tee /etc/systemd/system/heart-portal-staging-${service}.service > /dev/null << SERVICE_TEMPLATE
[Unit]
Description=Heart Portal Staging ${service^} Application
After=network.target

[Service]
Type=simple
User=heartportal
WorkingDirectory=/opt/heart-portal-staging/${dir}
Environment=PATH=/opt/heart-portal-staging/${dir}/venv/bin
ExecStart=/opt/heart-portal-staging/${dir}/venv/bin/python app.py
Restart=always
RestartSec=10
Environment=FLASK_ENV=staging
Environment=PORT=${port}
Environment=STAGING_MODE=true

[Install]
WantedBy=multi-user.target
SERVICE_TEMPLATE

done

# Create virtual environments and install dependencies
echo "Setting up virtual environments..."
for app_dir in main-app Nutrition-Database Food-Base Blog-Manager Sodium-Tracker Fluid-Tracker Weight-Tracker; do
    if [ -d "$STAGING_DIR/$app_dir" ]; then
        echo "Setting up $app_dir..."
        cd "$STAGING_DIR/$app_dir"

        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi

        source venv/bin/activate
        if [ -f "requirements.txt" ]; then
            pip install -q -r requirements.txt
        else
            pip install -q flask python-dotenv requests flask-session
        fi
        deactivate
    fi
done

# Reload systemd
sudo systemctl daemon-reload

# Stop any existing staging services
sudo systemctl stop heart-portal-staging-* 2>/dev/null || true

# Start staging services
echo "Starting staging services..."
for service in main nutrition food blog sodium fluid weight; do
    sudo systemctl start heart-portal-staging-$service
    sudo systemctl enable heart-portal-staging-$service
    echo "✅ Started heart-portal-staging-$service"
done

# Wait for services to start
sleep 5

# Check service status
echo "Checking staging service status..."
failed_services=""
for service in main nutrition food blog sodium fluid weight; do
    if ! sudo systemctl is-active --quiet heart-portal-staging-$service; then
        failed_services="$failed_services heart-portal-staging-$service"
    fi
done

if [ -n "$failed_services" ]; then
    echo "❌ Some services failed to start: $failed_services"
    for service in $failed_services; do
        echo "--- $service logs ---"
        sudo journalctl -u $service --lines=10 --no-pager
    done
    exit 1
fi

# Create nginx staging configuration
echo "Setting up nginx staging configuration..."
sudo tee /etc/nginx/sites-available/heart-portal-staging << 'NGINX_CONFIG'
server {
    listen 8081;
    server_name heartfailureportal.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /nutrition/ {
        proxy_pass http://localhost:5006/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /food/ {
        proxy_pass http://localhost:5007/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /blog/ {
        proxy_pass http://localhost:5008/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /sodium/ {
        proxy_pass http://localhost:5009/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /fluid/ {
        proxy_pass http://localhost:5010/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /weight/ {
        proxy_pass http://localhost:5011/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONFIG

# Enable staging site
sudo ln -sf /etc/nginx/sites-available/heart-portal-staging /etc/nginx/sites-enabled/heart-portal-staging

# Test nginx configuration
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx staging configuration activated"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

echo ""
echo "========================================"
echo "🎉 Staging Environment Ready!"
echo "========================================"
echo ""
echo "Staging URL: https://heartfailureportal.com:8081"
echo ""
echo "All staging services started successfully!"
echo "Production site continues running normally."
echo ""
SCRIPT_END
)

    # Execute staging deployment on server
    echo "$staging_script" | ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$SSH_KEY" heartportal@"$SERVER_HOST" 'cat > /tmp/staging_deploy.sh && chmod +x /tmp/staging_deploy.sh && /tmp/staging_deploy.sh && rm /tmp/staging_deploy.sh'
}

# Main staging deployment process
main() {
    echo "========================================"
    echo "🚀 Heart Portal Staging Deployment"
    echo "========================================"
    echo

    # Check environment
    if ! check_environment; then
        exit 1
    fi

    # Push branch to GitHub
    if ! push_branch_to_github; then
        exit 1
    fi

    # Deploy staging to server
    deploy_staging_to_server

    echo
    success "Staging deployment completed! 🎉"
    echo
    echo "🔧 Testing URLs:"
    echo "🌐 Staging Site: https://heartfailureportal.com:8081"
    echo "🌐 Production Site: https://heartfailureportal.com (unchanged)"
    echo
    echo "📊 Monitor staging services:"
    echo "ssh -i $SSH_KEY heartportal@$SERVER_HOST 'sudo systemctl status heart-portal-staging-*'"
    echo
    echo "🗑️  To remove staging when done:"
    echo "./scripts/cleanup-staging.sh"
    echo
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Heart Portal Staging Deployment Script"
        echo
        echo "Usage: ./deploy-staging.sh [command]"
        echo
        echo "Commands:"
        echo "  help        Show this help message"
        echo "  (no args)   Deploy multiuser-auth branch to staging"
        echo
        echo "This script will:"
        echo "1. Push multiuser-auth branch to GitHub"
        echo "2. Create staging environment at /opt/heart-portal-staging"
        echo "3. Set up separate systemd services (heart-portal-staging-*)"
        echo "4. Configure nginx on port 8081"
        echo "5. Copy production data for testing"
        echo
        echo "Staging URL: https://heartfailureportal.com:8081"
        echo "Production URL: https://heartfailureportal.com (unchanged)"
        ;;
    *)
        main "$@"
        ;;
esac