# Heart Portal Project

## Overview
Multi-component Flask application for heart failure nutrition management with USDA API integration.

## New Claude Session Quick Start

**Local Machine Role:**
- VSCode for editing code only
- Git for version control
- Local repo stays on **staging** branch
- **No local server, no PostgreSQL, no Gunicorn needed**

**Quick SSH Access:**
- Staging: `ssh heart-staging` (134.199.202.67)
- Production: `ssh heart-prod` (129.212.181.161)

**Common Commands:**
1. Edit code locally → `git add . && git commit -m "message" && git push origin staging`
2. Deploy to staging → `ssh heart-staging "cd /opt/heart-portal && git pull && sudo systemctl restart heart-portal-staging-*"`
3. Test staging → Open http://134.199.202.67 in browser
4. Deploy to production → Merge staging→production, then deploy

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

## Staging URLs (Development & Testing)
- Main App: http://134.199.202.67/
- Nutrition-Database: http://134.199.202.67/nutrition/
- Food-Base: http://134.199.202.67/food/
- Blog-Manager: http://134.199.202.67/blog/
- Sodium-Tracker: http://134.199.202.67/sodium/
- Fluid-Tracker: http://134.199.202.67/fluid/
- Weight-Tracker: http://134.199.202.67/weight/
- BP-Monitor: http://134.199.202.67/bp/

## Server Details

### Production Server
- Host: 129.212.181.161
- SSH: `ssh heart-prod` or `ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161`
- User: heartportal
- Project Path: /opt/heart-portal
- Git Branch: **production**
- Services: heart-portal-{main,nutrition,food,blog,sodium,fluid,weight,bp}
- Server Specs: 2 vCPU / 2GB RAM

### Staging Server
- Host: 134.199.202.67
- SSH: `ssh heart-staging` or `ssh -i /Users/mrrobot/.ssh/id_HFP_staging heartportal@134.199.202.67`
- User: heartportal
- Project Path: /opt/heart-portal
- Git Branch: **staging**
- Services: heart-portal-staging-{main,nutrition,food,blog,sodium,fluid,weight,bp}
- Server Specs: 1 vCPU / 1GB RAM
- Access: http://134.199.202.67 (HTTP only, no SSL yet)
- **Important**: `.env` file must contain `STAGING_BASE_URL=http://134.199.202.67` for correct URL generation

## Git Branch Strategy

The repository uses a three-tier branch system for managing deployments:

```
main                    # Main development branch
├── production         # Deployed to production server (129.212.181.161)
└── staging            # Deployed to staging server (134.199.202.67)
    └── feature-*      # Feature branches (merge to staging first)
```

### Branch Usage:
- **main**: Primary development branch, contains latest features
- **production**: Stable code deployed to production server (heartfailureportal.com)
- **staging**: Testing branch deployed to staging server (134.199.202.67)
- **postgres-migration**: Active development for PostgreSQL migration

### Deployment Workflow:
1. Develop features locally on feature branches
2. Merge to **staging** branch → Deploy to staging server for testing
3. After testing passes, merge to **production** branch → Deploy to production server
4. Keep **main** in sync with latest stable code

### Server Branch Configuration:
- Production server: Tracks **production** branch
- Staging server: Tracks **staging** branch

## Development Workflow

**New Workflow (2025-10-23):**
- **Local machine**: Code editor only (VSCode) - No PostgreSQL, no Gunicorn, no local server
- **Staging server**: All development, testing, and debugging happens here
- **Production server**: Stable releases only

### Step-by-Step Development Process

**1. Edit code locally in VSCode**
```bash
# Your local repo should always be on staging branch
git checkout staging
git pull origin staging

# Edit files in VSCode
# When done, commit locally
git add .
git commit -m "Description of changes"
```

**2. Push to GitHub and deploy to staging**
```bash
# Push changes to GitHub
git push origin staging

# SSH to staging server and pull changes
ssh heart-staging
cd /opt/heart-portal
git pull origin staging

# Restart services to apply changes
sudo systemctl restart heart-portal-staging-{main,nutrition,food,blog,sodium,fluid,weight,bp}

# Or restart specific service
sudo systemctl restart heart-portal-staging-main
exit
```

**3. Test on staging server**
```bash
# Access via browser: http://134.199.202.67
# Check logs if needed:
ssh heart-staging "sudo journalctl -u heart-portal-staging-main -n 50"
```

**4. When ready, deploy to production**
```bash
# Merge staging to production branch
git checkout production
git merge staging
git push origin production

# Deploy to production server
ssh heart-prod
cd /opt/heart-portal
git pull origin production
sudo systemctl restart heart-portal-{main,nutrition,food,blog,sodium,fluid,weight,bp}
exit

# Verify: https://heartfailureportal.com
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

### Scripts
- `scripts/deploy-venv.sh`: Deployment script with venv support (recommended)
- `scripts/deploy.sh`: Legacy deployment script
- `scripts/setup-venv-server.sh`: One-time server venv migration script
- `scripts/rollback.sh`: Production rollback script
- `scripts/dev-check.sh`: Environment verification
- `scripts/download-database.sh`: Database sync script
- `SCRIPTS.md`: Comprehensive documentation for all scripts

### Documentation
- `CLAUDE.md`: Development and deployment instructions (this file)
- `SERVER_VENV_SETUP.md`: Virtual environment migration guide
- `VENV_MIGRATION_QUICKSTART.md`: Quick start guide for venv migration
- `DB_MIGRATE_POSTGRES.md`: PostgreSQL migration plan
- `VENV_SETUP.md`: Local virtual environment documentation
- `QUICK_START.md`: Quick reference for common tasks

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
- ✅ **Fluid Tracker Fixed on Staging** - Fixed 5 critical issues: parameter name mismatches, database column naming, INSERT query missing updated_at, PostgreSQL sequence sync, and history page column reference (see FLUID_TRACKER_FIXES.md for details)
- ✅ **Form Button Standardization Complete** - All forms now follow Cancel (left) → Action (right) pattern with centered layout
- ✅ **Tracker Color Consistency** - Sodium Tracker and Weight Tracker action buttons now use blue (#2563eb)
- ✅ **History Page Action Buttons** - Added "Add Entry" buttons below content cards on Sodium, Fluid, and Weight History pages
- ✅ **Admin Navigation Cleanup** - Removed redundant navigation cards from admin pages, centered remaining elements
- ✅ **Virtual Environment Support** - Production and staging environments with isolated dependencies
- ✅ **Server Venv Migration** - Zero-downtime migration scripts and systemd service templates
- ✅ **Deployment Scripts Updated** - New `deploy-venv.sh` with staging/production support
- ✅ **Local Virtual Environment** - Full venv setup with requirements.txt for all dependencies
- ✅ **PostgreSQL Ready** - psycopg2 installed in venv, ready for database migration
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
- ✅ **Staging Server Setup** - Separate staging environment on dedicated server (134.199.202.67)
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
- ⚠️ **Blog Service on Staging** - PostgreSQL authentication issue (returns 500 error)
- Contact form exists but may need testing on staging

## Issues Recently Resolved
- ✅ **Fluid Tracker Add Entry Error** - Fixed parameter mismatch between app.py and database.py (time_consumed vs time_of_day)
- ✅ **Fluid Tracker Database Schema Mismatch** - Renamed columns to match code expectations (beverage_name, beverage_type, time_of_day)
- ✅ **Fluid Tracker INSERT Query** - Added missing updated_at column to prevent NOT NULL constraint violations
- ✅ **Fluid Tracker PostgreSQL Sequence** - Reset auto-increment sequence to prevent duplicate key errors
- ✅ **Fluid Tracker History Page KeyError** - Fixed column name reference from total_ml to total_volume
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

## Server Status

### Production Server (Last Checked)
- ✅ **heart-portal-main** (port 3000): Running normally
- ✅ **heart-portal-nutrition** (port 5000): Running normally
- ✅ **heart-portal-food** (port 5001): Running normally
- ✅ **heart-portal-blog** (port 5002): Running normally
- ✅ **heart-portal-sodium** (port 5003): Running normally
- ✅ **heart-portal-fluid** (port 5004): Running normally
- ✅ **heart-portal-weight** (port 5005): Running normally
- ✅ **heart-portal-bp** (port 5006): Running normally
- ✅ **Nginx & SSL**: Operating correctly with proper HTTPS redirects

### Staging Server (Last Checked)
- ✅ **heart-portal-staging-main** (port 3000): Running normally
- ✅ **heart-portal-staging-nutrition** (port 5000): Running normally
- ✅ **heart-portal-staging-food** (port 5001): Running normally
- ⚠️ **heart-portal-staging-blog** (port 5002): PostgreSQL auth issue (500 error)
- ✅ **heart-portal-staging-sodium** (port 5003): Running normally
- ✅ **heart-portal-staging-fluid** (port 5004): Running normally
- ✅ **heart-portal-staging-weight** (port 5005): Running normally
- ✅ **heart-portal-staging-bp** (port 5006): Running normally
- ✅ **Nginx**: Operating correctly (HTTP only, no SSL yet)

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

### Staging Server Issues
- Check service status: `ssh heart-staging "sudo systemctl status heart-portal-staging-*"`
- View logs: `ssh heart-staging "sudo journalctl -u heart-portal-staging-main -n 50"`
- Restart services: `ssh heart-staging "sudo systemctl restart heart-portal-staging-*"`
- Test services: `ssh heart-staging "curl -I http://localhost:3000"`

### Production Server Issues
- Check service status: `ssh heart-prod "sudo systemctl status heart-portal-*"`
- View logs: `ssh heart-prod "sudo journalctl -u heart-portal-main -n 50"`
- SSL issues: Use `./scripts/test-ssl.sh` to diagnose problems
- Certificate problems: Check `/var/log/heart-portal-ssl-renewal.log`

### General Troubleshooting
- Template errors: Check template files exist in correct directories
- Database issues: PostgreSQL connection problems in .env file
- Port conflicts on server: Check for existing processes with `sudo lsof -i :3000`

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

## UI Standardization (2025-01-11)

### Form Button Layout Standard
All forms across the application now follow a consistent button layout pattern:

**Pattern**: Cancel (left) → Action (right), centered layout

**Button Specifications**:
- **Cancel Button**: Gray (#6b7280), ✖ icon, on the left
- **Action Button**: Colored (blue #2563eb for trackers, green #10b981 for success actions), appropriate icon, on the right
- **Layout**: Centered with `justify-content: center;` and 15px gap
- **Icons**: ✖ for Cancel, 💾 for Save, ➕ for Add, 🔄 for Update, 🎯 for Set Goal

**Files Updated**:
- `Blog-Manager/templates/edit_post.html` - Added Cancel button, centered both buttons
- `Blog-Manager/templates/create_post.html` - Swapped positions, renamed "Save" to "Save Post"
- `BP-Monitor/templates/add_entry.html` - Swapped Cancel and Save Reading
- `BP-Monitor/templates/settings.html` - Swapped Cancel and Save Settings
- `Sodium-Tracker/templates/add_entry.html` - Swapped buttons, changed to blue (#2563eb)
- `Sodium-Tracker/templates/settings.html` - Swapped buttons, changed to blue, updated title
- `Fluid-Tracker/templates/add_entry.html` - Swapped Cancel and Add Entry
- `Fluid-Tracker/templates/settings.html` - Swapped Cancel and Save Settings
- `Weight-Tracker/templates/add_entry.html` - Swapped Cancel and Save Weight Entry
- `Weight-Tracker/templates/settings.html` - Swapped Cancel and Save Settings, changed to blue (#2563eb)
- `Weight-Tracker/templates/set_goal.html` - Swapped Cancel and Set Goal, changed to blue (#2563eb)

### Tracker Color Consistency
**Standard**: Sodium Tracker and Weight Tracker action buttons use blue (#2563eb) for consistency

**Files Updated**:
- `Sodium-Tracker/templates/add_entry.html` - Changed from red to blue
- `Sodium-Tracker/templates/settings.html` - Changed from red to blue
- `Sodium-Tracker/templates/history.html` - Add Entry button uses blue
- `Weight-Tracker/templates/settings.html` - Changed from green to blue
- `Weight-Tracker/templates/set_goal.html` - Changed from green to blue

### History Page Action Buttons
**Pattern**: "Add Entry" button below content card with 20px top margin

**Files Updated**:
- `Sodium-Tracker/templates/history.html` - Added "Add Sodium Entry" button below card
- `Fluid-Tracker/templates/history.html` - Added "Add Fluid Entry" button below card
- `Weight-Tracker/templates/history.html` - Added "Add Weight Entry" button below card, removed top action buttons

### Admin Navigation Cleanup
**Changes**: Removed redundant navigation cards and buttons, centered remaining elements

**Files Updated**:
- `main-app/templates/admin/dashboard.html`:
  - Removed Dashboard navigation card (redundant on dashboard page)
  - Removed User Dashboard button from Quick Actions
  - Centered User Management and Blog Moderation cards
  - Centered Quick Actions buttons
  - Removed `target="_blank"` from View Public Blog link
- `main-app/templates/admin/users.html`:
  - Removed Dashboard, User Management, and Blog Moderation navigation cards

### Standard Back Button Implementation
All standard back buttons follow:
- **Color**: Gray (#6c757d)
- **Icon**: Left arrow (fas fa-arrow-left)
- **Padding**: 10px 20px on button
- **Container Padding**: 40px top padding
- **Text**: "Back to [Destination]"

## Server Environment

### Python Dependencies
Both servers use system-wide Python packages (no virtual environments currently):
- Flask 3.1.2
- PostgreSQL adapter (psycopg2-binary 2.9.11)
- Gunicorn 23.0.0
- python-dotenv
- bcrypt
- flask-sqlalchemy (for Food-Base)
- werkzeug, jinja2, blinker, itsdangerous

### Production Server
- Python 3.10 (Ubuntu 22.04)
- PostgreSQL 14
- 2 vCPU / 2GB RAM

### Staging Server
- Python 3.12 (Ubuntu 24.04)
- PostgreSQL 16
- 1 vCPU / 1GB RAM

### Adding New Dependencies
To add a new Python package to staging:
```bash
ssh heart-staging "sudo pip3 install --break-system-packages package-name"
sudo systemctl restart heart-portal-staging-*
```

To add to production (after testing on staging):
```bash
ssh heart-prod "sudo pip3 install --break-system-packages package-name"
sudo systemctl restart heart-portal-*
```

## Documentation
- **README.md**: Comprehensive project documentation for GitHub display
- **CLAUDE.md**: Development and deployment instructions (this file)
- **Local vs Server**: README.md is excluded from server deployments but shows on GitHub repository