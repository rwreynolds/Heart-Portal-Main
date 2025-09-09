# Heart Portal Project

## Overview
Multi-component Flask application for heart failure nutrition management with USDA API integration.

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
- SSH Key: ./Food-Base/heart_portal_key
- Project Path: /opt/heart-portal
- Services: Managed via systemctl (heart-portal-main, heart-portal-nutrition, heart-portal-food, heart-portal-blog)

## Development Workflow
**CRITICAL: All changes must be made locally, never on the server**

### Before Making Changes
```bash
./dev-check.sh  # Verify you're in local environment
```

### Deployment Process
```bash
./deploy.sh     # Push to GitHub and deploy to server
```

### Database Management
```bash
./download-database.sh  # Download production database to local
```

## Key Files
- `main-app/main_app.py`: Main Flask application
- `Nutrition-Database/app.py`: Nutrition database Flask app
- `Food-Base/app.py`: Food storage Flask app
- `Blog-Manager/app.py`: Blog system Flask app
- `deploy.sh`: Local deployment script
- `dev-check.sh`: Environment verification
- `download-database.sh`: Database sync script

## Environment Variables
- USDA API Key required in `.env` files for each component
- Database files excluded from git (preserved during deployment)

## Safety Features
- Environment checks prevent server-side editing
- Database preservation during deployments
- Automated health checks after deployment
- Git workflow enforcement

## Recent Changes
- Header background changed to red (#dc2626) in main app
- Environment-aware JavaScript for local/production compatibility
- Fixed deployment script syntax errors
- Implemented database-safe deployment workflow

## Current Issues
- Missing error templates (404.html, 500.html) referenced in main_app.py
- Contact form exists but may need testing

## Templates Status
### Main App Templates (main-app/templates/)
- ✅ landing.html - Main landing page with red header
- ✅ about.html - About the portal page  
- ✅ creator.html - About creator page
- ✅ contact.html - Contact form page
- ❌ 404.html - Missing (referenced in error handler)
- ❌ 500.html - Missing (referenced in error handler)

## Application Routes
### Main App (main-app/main_app.py)
- `/` - Landing page
- `/about` - About portal
- `/creator` - About creator  
- `/contact` - Contact form (GET/POST)
- `/blog` - Redirects to blog manager (port 5002)
- `/redirect/nutrition` - Redirects to API Manager
- `/redirect/foodbase` - Redirects to Food-Base

## Troubleshooting
- Use `./dev-check.sh` to verify environment
- Check service status on server: `systemctl status heart-portal-*`
- Database issues: Use `./download-database.sh` to sync from production
- Deployment hanging: SSH connection uses BatchMode and ConnectTimeout
- Template errors: Check template files exist in correct directories