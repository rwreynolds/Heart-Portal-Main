# Heart Portal Project

## Overview
Multi-component Flask application for heart failure nutrition management with USDA API integration.

## New Claude Session Quick Start
**For Claude to help with server tasks, just tell Claude:**
1. "Check the server status" → I'll use `./scripts/monitor.sh all --local`
2. "Deploy changes" → I'll use `./scripts/deploy.sh`
3. "Fix service issues" → I'll use `./scripts/troubleshoot.sh full --fix`
4. "Manage services" → I'll use `./scripts/manage-services.sh` commands
5. Server connection: `ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161`

## Architecture
- **Main App** (port 3000): Landing page, about pages, navigation hub
- **Nutrition-Database** (port 5000): USDA Food Data Central API interface
- **Food-Base** (port 5001): Personal food storage and management
- **Blog-Manager** (port 5002): Heart health blog system
- **Sodium-Tracker** (port 5003): Daily sodium intake tracking for heart failure patients
- **Fluid-Tracker** (port 5004): Daily fluid intake monitoring for optimal hydration
- **Weight-Tracker** (port 5005): Daily weight tracking for heart failure monitoring

## Production URLs
- Main Site: https://heartfailureportal.com
- Nutrition-Database: https://heartfailureportal.com/nutrition-database/
- Food-Base: https://heartfailureportal.com/food-base/
- Blog-Manager: https://heartfailureportal.com/blog-manager/
- Sodium-Tracker: https://heartfailureportal.com/sodium-tracker/
- Fluid-Tracker: https://heartfailureportal.com/fluid-tracker/
- Weight-Tracker: https://heartfailureportal.com/weight-tracker/

## Local Development URLs
- Main App: http://localhost:3000
- Nutrition-Database: http://localhost:5000
- Food-Base: http://localhost:5001
- Blog-Manager: http://localhost:5002
- Sodium-Tracker: http://localhost:5003
- Fluid-Tracker: http://localhost:5004
- Weight-Tracker: http://localhost:5005

## Server Details
- Host: 129.212.181.161
- SSH Key: /Users/mrrobot/.ssh/id_ed25519
- User: heartportal
- Project Path: /opt/heart-portal
- Services: Managed via systemctl (heart-portal-main, heart-portal-nutrition, heart-portal-food, heart-portal-blog, heart-portal-sodium, heart-portal-fluid, heart-portal-weight)

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

### Service Management (New Consolidated Scripts)
```bash
# Service control
./scripts/manage-services.sh status              # Check all services
./scripts/manage-services.sh restart             # Restart all services
./scripts/manage-services.sh start main          # Start main app only
./scripts/manage-services.sh update              # Fix main service port conflicts

# Monitoring & diagnostics
./scripts/monitor.sh all                         # Quick status check
./scripts/monitor.sh main                        # Detailed main app status
./scripts/troubleshoot.sh full                   # Complete system diagnostic
./scripts/troubleshoot.sh port --fix             # Diagnose and fix port issues
```

## Key Files
- `main-app/main_app.py`: Main Flask application
- `Nutrition-Database/app.py`: Nutrition database Flask app
- `Food-Base/app.py`: Food storage Flask app
- `Blog-Manager/app.py`: Blog system Flask app
- `README.md`: GitHub repository documentation (excluded from server)
- `scripts/deploy.sh`: Local deployment script
- `scripts/rollback.sh`: Production rollback script
- `scripts/dev-check.sh`: Environment verification
- `scripts/download-database.sh`: Database sync script
- `SCRIPTS.md`: Comprehensive documentation for all scripts (see for detailed usage)

## SSL/HTTPS Configuration
- `nginx/heart-portal.conf`: Nginx reverse proxy configuration
- `scripts/setup-ssl.sh`: One-time SSL setup script (run on server)
- `scripts/renew-ssl.sh`: Manual SSL certificate renewal
- `scripts/test-ssl.sh`: SSL/HTTPS testing and verification
- `scripts/monitor.sh`: Health monitoring for all services
- `scripts/manage-services.sh`: Service lifecycle management
- `scripts/troubleshoot.sh`: Comprehensive diagnostics and auto-repair

## Environment Variables
- USDA API Key required in `.env` files for each component
- Database files excluded from git (preserved during deployment)

## Safety Features
- Environment checks prevent server-side editing
- Database preservation during deployments
- Automated health checks after deployment
- Git workflow enforcement

## Recent Changes
- ✅ **Script Consolidation** - Reduced 19 scripts to 12 (-37%), eliminated overlaps and conflicts
- ✅ **New Consolidated Scripts** - `manage-services.sh`, `monitor.sh`, `troubleshoot.sh` with enhanced features
- ✅ **Script Organization** - All scripts moved to `scripts/` folder with updated cross-references
- ✅ **Production Rollback System** - `scripts/rollback.sh` script with safety checks and recovery tags
- ✅ **Enhanced Monitoring** - `scripts/monitor.sh` works locally to monitor remote server with health scoring
- ✅ **SSL/HTTPS fully configured** with Let's Encrypt certificates
- ✅ **Sticky navigation** implemented across all applications
- ✅ **Fixed deployment script** with correct SSH key paths and server sync
- ✅ **All error templates created** (404.html, 500.html) for all applications
- ✅ **README.md Documentation** - Comprehensive project documentation created for GitHub repository
- ✅ **Server Analysis Complete** - Full production server architecture documented
- ✅ **Local Development Setup** - Main app can run locally on port 3000
- ✅ **Navbar Consistency Fixed** - All applications now have unified Tools → Trackers submenu structure
- ✅ **About Page CSS Fixed** - Removed overflow:hidden that prevented submenu display
- ✅ **Weight-Tracker Fixed** - Resolved close_db() TypeError and blank page issues
- ✅ **Component Template Updates** - All Flask apps now have consistent navbar and redirect routes
- ✅ **Template Inheritance Implementation** - Converted all applications to use shared template system
- ✅ **Medical Disclaimer Warnings** - Bright orange warning notices added to all applications
- ✅ **Blog-Manager Template Conversion** - Converted from standalone HTML to template inheritance
- ✅ **Nutrition Database Styling Fixes** - Fixed fake header overlay and hero section consistency
- ✅ **Form Layout Consistency** - Fixed Data Types section styling in Advanced Food Search
- ✅ **Tab Navigation Styling** - Enhanced visibility of inactive tab buttons for better user experience
- ✅ **Page Styling Standardization** - Unified hero sections and content sections across all Main App pages
- Header background changed to red (#dc2626) in main app
- Environment-aware JavaScript for local/production compatibility
- Fixed deployment script syntax errors
- Implemented database-safe deployment workflow
- README.md excluded from server deployments via .gitignore but available for GitHub display

## Current Issues
- ⚠️ **Server Main App Service** - heart-portal-main service experiencing restart loop (port conflict resolved locally)
- Contact form exists but may need testing
- Consider upgrading to production WSGI server (currently using Flask dev server)

## Issues Recently Resolved
- ✅ **Navbar Inconsistency** - Fixed Tools dropdown structure across all applications
- ✅ **About Page Submenu** - Fixed CSS overflow issue preventing Trackers submenu display
- ✅ **Weight-Tracker Service** - Fixed close_db() TypeError and blank page issues
- ✅ **Missing Redirect Routes** - Added tracker redirect routes to all component applications
- ✅ **Template Inheritance Missing** - All applications now properly extend shared base.html template
- ✅ **Medical Disclaimer Missing** - Bright orange warning notices now appear on all pages
- ✅ **Blog-Manager Standalone HTML** - Converted to template inheritance with proper CSS blocks
- ✅ **Nutrition Database Header Issues** - Removed fake header div that was hiding shared navigation
- ✅ **Inconsistent Hero Sections** - Standardized hero section styling across applications
- ✅ **Form Element Styling** - Data Types section now matches other Advanced Search form elements
- ✅ **Tab Button Visibility** - Inactive tabs now clearly visible instead of appearing disabled
- ✅ **Inconsistent Page Layouts** - Standardized hero sections (20px top padding) and content sections (80px padding) across all Main App pages

## Known Server Status (Last Checked)
- ✅ **heart-portal-nutrition** (port 5000): Running normally
- ✅ **heart-portal-food** (port 5001): Running normally
- ✅ **heart-portal-blog** (port 5002): Running normally
- ❌ **heart-portal-main** (port 3000): Service failing due to port conflict with existing process
- ✅ **heart-portal-sodium** (port 5003): Running normally
- ✅ **heart-portal-fluid** (port 5004): Running normally
- ✅ **heart-portal-weight** (port 5005): Running normally (recently fixed)
- ✅ **Nginx & SSL**: Operating correctly with proper HTTPS redirects

## Local Development Status (Current Session)
- ✅ **Main App** (port 3000): Running successfully
- ✅ **Weight-Tracker** (port 5005): Fixed and running (close_db issue resolved)
- ✅ **All Applications**: Consistent navbar with unified Tools → Trackers submenu
- ✅ **About Page**: CSS submenu display issue resolved

## Templates Status
### Main App Templates (main-app/templates/)
- ✅ landing.html - Main landing page with standardized hero (20px padding) and sticky navigation
- ✅ about.html - About portal page with standardized content section (80px padding)
- ✅ creator.html - About creator page with standardized content section (80px padding)
- ✅ contact.html - Contact form page with standardized content section (80px padding)
- ✅ 404.html - Error page with sticky navigation
- ✅ 500.html - Error page with sticky navigation

### Admin Templates (main-app/templates/admin/)
- ✅ blog.html - Blog moderation page with 20px title padding (no red border)
- ✅ dashboard.html - System administration page with 20px title padding (no red border)
- ✅ users.html - User management page with 20px title padding (no red border)

### All Applications Feature Status
- ✅ **Sticky Navigation** - Fixed header across all apps and pages
- ✅ **Template Inheritance** - All applications now extend shared base.html template system
- ✅ **Medical Disclaimer** - Bright orange warning notices display on all pages
- ✅ **HTTPS/SSL** - Let's Encrypt certificates configured
- ✅ **Error Pages** - 404/500 templates in all applications
- ✅ **Responsive Design** - Mobile-friendly layouts
- ✅ **Consistent Styling** - Unified form layouts and navigation across all components

## Application Routes
### Main App (main-app/main_app.py)
- `/` - Landing page
- `/about` - About portal
- `/creator` - About creator
- `/contact` - Contact form (GET/POST)
- `/blog` - Redirects to blog manager (port 5002)
- `/redirect/nutrition` - Redirects to Nutrition Database (port 5000)
- `/redirect/foodbase` - Redirects to Food-Base (port 5001)
- `/redirect/sodium` - Redirects to Sodium Tracker (port 5003)
- `/redirect/fluid` - Redirects to Fluid Tracker (port 5004)
- `/redirect/weight` - Redirects to Weight Tracker (port 5005)

### Navigation Structure
All applications feature unified navigation:
- **Tools** dropdown containing:
  - 🔍 Nutrition Database
  - 🍎 Food Storage
  - **📊 Trackers ▶** (submenu)
    - 🧂 Sodium Tracker
    - 💧 Fluid Tracker
    - ⚖️ Weight Tracker

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
- **Local Port Conflicts**: If port 3000 is in use locally, kill processes with `lsof -ti :3000` then `kill -9 <PID>`
- **Server Main App Issues**: Check for existing processes holding port 3000 on server

### Recently Fixed Issues (Reference)
- **Navbar Inconsistency**: Fixed by updating all component templates with unified Tools → Trackers structure
- **About Page Submenu Not Showing**: Fixed by removing `overflow: hidden` from `.content` CSS class in `about.html:125`
- **Weight-Tracker Blank Page**: Fixed Flask `close_db()` TypeError by renaming teardown function to avoid naming conflicts
- **Missing Tracker Redirects**: Added `/redirect/sodium`, `/redirect/fluid`, `/redirect/weight` routes to all component applications
- **BuildError for Tracker URLs**: Fixed by ensuring all templates have the required `url_for()` redirect routes
- **Inconsistent Page Layouts**: Standardized hero sections and content sections across all Main App pages with consistent padding and structure

## Page Styling Standards

### Hero Sections
All hero sections across the application follow these standards:
- **Top Padding**: 20px (applied via inline style: `style="padding-top: 20px !important;"`)
- **Base Padding**: `padding: 60px 0 40px;` (vertical centering)
- **Text Color**: White
- **Title Font Size**: `3rem` with `text-shadow: 2px 2px 4px rgba(0,0,0,0.3)`
- **Subtitle Font Size**: `1.2rem` with `text-shadow: 1px 1px 2px rgba(0,0,0,0.3)`
- **Structure**: `<section class="hero"><div class="main-container">...</div></section>`

### Content Sections
All content sections follow these standards:
- **Padding**: `padding: 80px 0;` (vertical spacing, no horizontal)
- **Background**: `background: white;`
- **Width Control**: `<section class="content"><div class="main-container">...</div></section>`
- **Max Width**: 1200px (from `.main-container`)
- **Heading Color**: `color: #667eea;` (purple accent)
- **Text Line Height**: `line-height: 1.8;`

### Admin Page Titles
All admin pages follow these standards:
- **Top Padding**: 20px (applied via inline style: `style="padding-top: 20px !important;"`)
- **Border**: No red border under titles (previously removed)
- **Header Margin**: `margin-top: 60px;` (clearance for fixed navbar)

### Pages Using These Standards
- **Main App**: landing.html, about.html, creator.html, contact.html
- **Admin Pages**: blog.html, dashboard.html, users.html
- **Blog Manager**: blog.html (hero section)
- **Nutrition Database**: index.html (hero section with gradient background)

### Implementation Notes
- Use inline `style="padding-top: 20px !important;"` for hero sections to override base styles
- Use `<section class="content"><div class="main-container">` structure for proper width control
- Avoid nested `.content-body` divs within `.content` sections
- CSS selectors should target `.content h2`, `.content p`, etc. directly

## Documentation
- **README.md**: Comprehensive project documentation for GitHub display
- **CLAUDE.md**: Development and deployment instructions (this file)
- **Local vs Server**: README.md is excluded from server deployments but shows on GitHub repository