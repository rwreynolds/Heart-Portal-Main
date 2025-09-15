# Heart Portal Project

## Overview
Multi-component Flask application for heart failure nutrition management with USDA API integration.

## New Claude Session Quick Start
**For Claude to help with server tasks, just tell Claude:**
1. "Check the server status" → I'll use the connection details below
2. "Deploy SSL" → I'll use `./scripts/deploy.sh` then guide you through server setup
3. "Monitor services" → I'll help run `./scripts/monitor-services.sh` on server
4. Server connection: `ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161`

## Architecture
- **Main App** (port 3000): Landing page, about pages, navigation hub
- **Nutrition-Database** (port 5000): USDA Food Data Central API interface
- **Food-Base** (port 5001): Personal food storage and management
- **Blog-Manager** (port 5002): Heart health blog system

## Production URLs
- Main Site: https://heartfailureportal.com
- Nutrition-Database: https://heartfailureportal.com/nutrition-database/
- Food-Base: https://heartfailureportal.com/food-base/
- Blog-Manager: https://heartfailureportal.com/blog-manager/

## Local Development URLs
- Main App: http://localhost:3000
- Nutrition-Database: http://localhost:5000
- Food-Base: http://localhost:5001
- Blog-Manager: http://localhost:5002

## Server Details
- Host: 129.212.181.161
- SSH Key: /Users/mrrobot/.ssh/id_ed25519
- User: heartportal
- Project Path: /opt/heart-portal
- Services: Managed via systemctl (heart-portal-main, heart-portal-nutrition, heart-portal-food, heart-portal-blog)

### Server Connection
```bash
./scripts/connect-server.sh                    # Quick SSH connection
ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161
```

## Development Workflow
**CRITICAL: All changes must be made locally, never on the server**

### Before Making Changes
```bash
./scripts/dev-check.sh  # Verify you're in local environment
```

### Deployment Process
```bash
./scripts/deploy.sh     # Push to GitHub and deploy to server
```

### Production Rollback
```bash
./scripts/rollback.sh              # Rollback to previous version
./scripts/rollback.sh --force      # Force rollback without safety checks
./scripts/rollback.sh --commit abc123  # Rollback to specific commit
```

### Database Management
```bash
./scripts/download-database.sh  # Download production database to local
```

## Key Files
- `main-app/main_app.py`: Main Flask application
- `Nutrition-Database/app.py`: Nutrition database Flask app
- `Food-Base/app.py`: Food storage Flask app
- `Blog-Manager/app.py`: Blog system Flask app
- `scripts/deploy.sh`: Local deployment script
- `scripts/rollback.sh`: Production rollback script
- `scripts/dev-check.sh`: Environment verification
- `scripts/download-database.sh`: Database sync script

## SSL/HTTPS Configuration
- `nginx/heart-portal.conf`: Nginx reverse proxy configuration
- `scripts/setup-ssl.sh`: One-time SSL setup script (run on server)
- `scripts/renew-ssl.sh`: Manual SSL certificate renewal
- `scripts/test-ssl.sh`: SSL/HTTPS testing and verification
- `scripts/monitor-services.sh`: Health monitoring for all services

## Environment Variables
- USDA API Key required in `.env` files for each component
- Database files excluded from git (preserved during deployment)

## Safety Features
- Environment checks prevent server-side editing
- Database preservation during deployments
- Automated health checks after deployment
- Git workflow enforcement

## Recent Changes
- ✅ **Script Organization** - All scripts moved to `scripts/` folder with updated cross-references
- ✅ **Production Rollback System** - `scripts/rollback.sh` script with safety checks and recovery tags
- ✅ **Enhanced Monitoring** - `scripts/monitor-services.sh` works locally to monitor remote server
- ✅ **SSL/HTTPS fully configured** with Let's Encrypt certificates
- ✅ **Sticky navigation** implemented across all applications
- ✅ **Fixed deployment script** with correct SSH key paths and server sync
- ✅ **All error templates created** (404.html, 500.html) for all applications
- Header background changed to red (#dc2626) in main app
- Environment-aware JavaScript for local/production compatibility
- Fixed deployment script syntax errors
- Implemented database-safe deployment workflow

## Current Issues
- Contact form exists but may need testing
- Consider upgrading to production WSGI server (currently using Flask dev server)

## Templates Status
### Main App Templates (main-app/templates/)
- ✅ landing.html - Main landing page with red header & sticky navigation
- ✅ about.html - About the portal page with sticky navigation
- ✅ creator.html - About creator page with sticky navigation
- ✅ contact.html - Contact form page with sticky navigation
- ✅ 404.html - Error page with sticky navigation
- ✅ 500.html - Error page with sticky navigation

### All Applications Feature Status
- ✅ **Sticky Navigation** - Fixed header across all apps and pages
- ✅ **HTTPS/SSL** - Let's Encrypt certificates configured
- ✅ **Error Pages** - 404/500 templates in all applications
- ✅ **Responsive Design** - Mobile-friendly layouts

## Application Routes
### Main App (main-app/main_app.py)
- `/` - Landing page
- `/about` - About portal
- `/creator` - About creator  
- `/contact` - Contact form (GET/POST)
- `/blog` - Redirects to blog manager (port 5002)
- `/redirect/nutrition` - Redirects to API Manager
- `/redirect/foodbase` - Redirects to Food-Base

## SSL Setup Instructions
**One-time setup on server (after deploying scripts):**
```bash
# Deploy SSL configuration files
./scripts/deploy.sh

# SSH to server and run SSL setup
ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161
sudo ./scripts/setup-ssl.sh
```

**SSL Management Commands:**
```bash
./scripts/monitor-services.sh    # Check all services including HTTPS
./scripts/test-ssl.sh           # Comprehensive SSL testing
./scripts/renew-ssl.sh          # Manual certificate renewal
./scripts/renew-ssl.sh --force  # Force renewal
```

## Complete Deploy → Test → Rollback Workflow
**All commands run from local machine:**

### 1. Deploy & Test
```bash
./scripts/deploy.sh              # Deploy changes to production
./scripts/monitor-services.sh    # Verify all services are healthy
```

### 2. If Issues Found - Rollback
```bash
./scripts/rollback.sh            # Quick rollback to previous version
./scripts/rollback.sh --force    # Force rollback without health checks
```

### 3. Fix Locally & Redeploy
```bash
# Fix issues in local development
./scripts/deploy.sh              # Deploy fixed version
```

## Troubleshooting
- Use `./scripts/dev-check.sh` to verify environment
- Check service status on server: `systemctl status heart-portal-*`
- Database issues: Use `./scripts/download-database.sh` to sync from production
- Deployment hanging: SSH connection uses BatchMode and ConnectTimeout
- Template errors: Check template files exist in correct directories
- SSL issues: Use `./scripts/test-ssl.sh` to diagnose problems
- Certificate problems: Check `/var/log/heart-portal-ssl-renewal.log`