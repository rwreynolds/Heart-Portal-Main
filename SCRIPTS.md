# Heart Portal Scripts Documentation

## Overview

This document provides comprehensive documentation for the Heart Portal consolidated script system. All scripts are designed for efficient management of the multi-component Flask application ecosystem.

**Total Scripts: 12** (reduced from 19 - eliminated 7 duplicate/overlapping scripts)

---

## 🚀 Consolidated Scripts (Primary Tools)

### 🔧 `manage-services.sh` - Complete Service Management
**Replaces:** `start-system.sh`, `stop-system.sh`, `status-system.sh`, `update-main-service.sh`

#### **All Available Commands:**

```bash
# === PRODUCTION SERVICE OPERATIONS (DEFAULT) ===
./scripts/manage-services.sh start               # Start all production services (remote)
./scripts/manage-services.sh stop                # Stop all production services (remote)
./scripts/manage-services.sh restart             # Restart all production services (remote)
./scripts/manage-services.sh status              # Show status of all production services (remote)

# === STAGING SERVICE OPERATIONS ===
./scripts/manage-services.sh start --staging     # Start all staging services (remote)
./scripts/manage-services.sh stop --staging      # Stop all staging services (remote)
./scripts/manage-services.sh restart --staging   # Restart all staging services (remote)
./scripts/manage-services.sh status --staging    # Show status of all staging services (remote)

# === INDIVIDUAL SERVICE CONTROL ===
./scripts/manage-services.sh start [service]     # Start specific production service
./scripts/manage-services.sh stop [service]      # Stop specific production service
./scripts/manage-services.sh restart [service]   # Restart specific production service
./scripts/manage-services.sh status [service]    # Check specific production service status

# === STAGING INDIVIDUAL SERVICE CONTROL ===
./scripts/manage-services.sh start [service] --staging     # Start specific staging service
./scripts/manage-services.sh stop [service] --staging      # Stop specific staging service
./scripts/manage-services.sh restart [service] --staging   # Restart specific staging service
./scripts/manage-services.sh status [service] --staging    # Check specific staging service status

# === LOCAL DEVELOPMENT MODE ===
./scripts/manage-services.sh start --local       # Start all services locally (Flask processes)
./scripts/manage-services.sh stop --local        # Stop all local Flask processes
./scripts/manage-services.sh restart --local     # Restart all local Flask processes
./scripts/manage-services.sh status --local      # Show local Flask process status
./scripts/manage-services.sh start [service] --local    # Start specific service locally
./scripts/manage-services.sh stop [service] --local     # Stop specific local service
./scripts/manage-services.sh restart [service] --local  # Restart specific local service
./scripts/manage-services.sh status [service] --local   # Check specific local service

# === SERVICE UPDATES (REMOTE ONLY) ===
./scripts/manage-services.sh update              # Update main production service (fix port conflicts)
```

#### **Service Names:**
- `main` - Heart Portal main app (port 3000)
- `nutrition` - Nutrition Database (port 5000)
- `food` - Food-Base storage (port 5001)
- `blog` - Blog Manager (port 5002)
- `sodium` - Sodium Tracker (port 5003)
- `fluid` - Fluid Tracker (port 5004)
- `weight` - Weight Tracker (port 5005)
- `bp` - BP Monitor (port 5006)

#### **Examples:**

**Production Service Operations (Default):**
```bash
# Start only the main app and nutrition database on production server
./scripts/manage-services.sh start main
./scripts/manage-services.sh start nutrition

# Check status of tracker services on production server
./scripts/manage-services.sh status sodium
./scripts/manage-services.sh status fluid
./scripts/manage-services.sh status weight

# Restart problematic service on production server
./scripts/manage-services.sh restart main

# Fix main app port conflicts on production server
./scripts/manage-services.sh update
```

**Staging Service Operations:**
```bash
# Restart all staging services (e.g., after deployment)
./scripts/manage-services.sh restart --staging

# Check status of all staging services
./scripts/manage-services.sh status --staging

# Restart specific staging service
./scripts/manage-services.sh restart sodium --staging
./scripts/manage-services.sh restart blog --staging

# Start/stop staging environment
./scripts/manage-services.sh start --staging
./scripts/manage-services.sh stop --staging
```

**Local Development Operations:**
```bash
# Start all services locally for development (Flask processes)
./scripts/manage-services.sh start --local

# Start specific services locally
./scripts/manage-services.sh start blog --local
./scripts/manage-services.sh start main --local

# Check local development status
./scripts/manage-services.sh status --local
./scripts/manage-services.sh status blog --local

# Restart local services (useful for testing changes)
./scripts/manage-services.sh restart blog --local
./scripts/manage-services.sh restart --local

# Stop all local development services
./scripts/manage-services.sh stop --local
```

**Mixed Operations:**
```bash
# Check production server status
./scripts/manage-services.sh status

# Check staging status
./scripts/manage-services.sh status --staging

# Deploy to staging and restart
./scripts/deploy-staging-simple.sh
./scripts/manage-services.sh restart --staging

# Test locally, then deploy to production
./scripts/manage-services.sh stop --local
./scripts/deploy.sh
./scripts/manage-services.sh restart
```

#### **Features:**
- ✅ **Triple Environment Support**: Production, staging, and local development
- ✅ **Staging Environment**: `--staging` flag manages `heart-portal-staging-*` services
- ✅ **Production Environment**: Default mode manages `heart-portal-*` services
- ✅ **Local Development Mode**: `--local` flag for Flask process management
- ✅ **Unified service lifecycle management**: start, stop, restart, status operations
- ✅ **Individual or bulk service operations**: Target specific services or manage all at once
- ✅ **Automatic port conflict resolution**: Built-in port 3000 conflict detection and resolution
- ✅ **Environment detection**: Automatically detects local vs remote execution context
- ✅ **Health verification**: Post-operation service health checks and port connectivity tests
- ✅ **Systemd integration**: Full systemd service management for production/staging deployment
- ✅ **Error handling and recovery**: Comprehensive error reporting and auto-recovery features

---

### 📊 `monitor.sh` - Service Monitoring & Health Checks
**Replaces:** `monitor-services.sh`, `monitor-main-app.sh`

#### **All Available Commands:**

```bash
# === BASIC MONITORING ===
./scripts/monitor.sh all                         # Monitor all services (quick check)
./scripts/monitor.sh [service]                   # Monitor specific service (detailed)

# === EXECUTION MODES ===
./scripts/monitor.sh all --local                 # Monitor from local machine (default)
./scripts/monitor.sh all --remote                # Monitor directly on server

# === ADVANCED MONITORING ===
./scripts/monitor.sh continuous                  # Start continuous monitoring with auto-restart
./scripts/monitor.sh continuous --interval 30    # Custom monitoring interval (seconds)
./scripts/monitor.sh health                      # Full health assessment with scoring

# === SPECIALIZED CHECKS ===
./scripts/monitor.sh ssl                         # SSL certificate monitoring only
./scripts/monitor.sh performance                 # Performance metrics only
./scripts/monitor.sh logs                        # Real-time log monitoring
```

#### **Monitor Targets:**
- `all` - All Heart Portal services + nginx + SSL
- `main` - Main app detailed monitoring
- `nutrition` - Nutrition Database monitoring
- `food` - Food-Base monitoring
- `blog` - Blog Manager monitoring
- `sodium` - Sodium Tracker monitoring
- `fluid` - Fluid Tracker monitoring
- `weight` - Weight Tracker monitoring
- `bp` - BP Monitor monitoring
- `nginx` - Nginx reverse proxy monitoring
- `ssl` - SSL certificate monitoring

#### **Examples:**
```bash
# Quick status check of all services
./scripts/monitor.sh all

# Detailed monitoring of main app
./scripts/monitor.sh main

# Monitor from local machine (checks remote server)
./scripts/monitor.sh all --local

# Continuous monitoring with auto-restart
./scripts/monitor.sh continuous

# Check only SSL certificate status
./scripts/monitor.sh ssl

# Monitor tracker services specifically
./scripts/monitor.sh sodium
./scripts/monitor.sh fluid
./scripts/monitor.sh weight
./scripts/monitor.sh bp
```

#### **Features:**
- ✅ Health scoring system (0-100%)
- ✅ Automatic service restart on failure
- ✅ SSL certificate monitoring
- ✅ Response time measurements
- ✅ Memory usage tracking
- ✅ Configurable monitoring intervals
- ✅ Real-time alerts and notifications
- ✅ Performance metrics collection

---

### 🔍 `troubleshoot.sh` - Comprehensive Diagnostics & Auto-Repair
**Replaces:** `diagnose-port-3000.sh`, `safe-server-test.sh`, `test-solution.sh`

#### **All Available Commands:**

```bash
# === SPECIFIC DIAGNOSTICS ===
./scripts/troubleshoot.sh port                   # Port 3000 conflict diagnosis
./scripts/troubleshoot.sh services               # Service health testing
./scripts/troubleshoot.sh ssl                    # SSL/HTTPS validation
./scripts/troubleshoot.sh network                # Network connectivity tests
./scripts/troubleshoot.sh system                 # System health check
./scripts/troubleshoot.sh database               # Database connectivity tests
./scripts/troubleshoot.sh permissions            # File permissions validation

# === COMPREHENSIVE TESTING ===
./scripts/troubleshoot.sh full                   # Complete system diagnostic
./scripts/troubleshoot.sh quick                  # Fast essential checks only

# === AUTO-REPAIR MODES ===
./scripts/troubleshoot.sh port --fix             # Diagnose and fix port issues
./scripts/troubleshoot.sh services --fix         # Test and repair services
./scripts/troubleshoot.sh ssl --fix              # Fix SSL certificate issues
./scripts/troubleshoot.sh full --fix             # Complete diagnostic with auto-repair

# === REPORTING ===
./scripts/troubleshoot.sh report                 # Generate diagnostic report
./scripts/troubleshoot.sh report --email         # Email diagnostic report
```

#### **Diagnostic Areas:**
- `port` - Port 3000 conflicts and availability
- `services` - All Heart Portal service health
- `ssl` - SSL certificates and HTTPS configuration
- `network` - Connectivity and DNS resolution
- `system` - Server resources and performance
- `database` - Database files and permissions
- `permissions` - File system permissions
- `nginx` - Nginx configuration and proxy setup

#### **Examples:**
```bash
# Diagnose and fix port 3000 conflicts
./scripts/troubleshoot.sh port --fix

# Complete system diagnostic
./scripts/troubleshoot.sh full

# Quick essential checks only
./scripts/troubleshoot.sh quick

# Test and repair all services
./scripts/troubleshoot.sh services --fix

# Validate SSL certificate setup
./scripts/troubleshoot.sh ssl

# Check database connectivity
./scripts/troubleshoot.sh database

# Generate comprehensive diagnostic report
./scripts/troubleshoot.sh report
```

#### **Features:**
- ✅ Port conflict detection and resolution
- ✅ Service health validation
- ✅ SSL certificate verification
- ✅ Network connectivity testing
- ✅ System resource monitoring
- ✅ Automatic repair capabilities
- ✅ Detailed diagnostic reporting
- ✅ Database connectivity checks
- ✅ Permission validation
- ✅ Configuration file validation

---

## 🚀 Core Deployment Scripts

### `deploy.sh` - Main Deployment Pipeline

#### **Command:**
```bash
./scripts/deploy.sh                              # Deploy all changes to production
./scripts/deploy.sh --help                       # Show deployment help
```

#### **What It Does:**
1. **Environment Check** - Verifies you're working locally
2. **Git Management** - Prompts to commit uncommitted changes
3. **GitHub Push** - Pushes commits to remote repository
4. **Server Deployment** - Syncs files to production server
5. **Service Restart** - Restarts all affected services
6. **Health Verification** - Confirms deployment success
7. **Recovery Tags** - Creates rollback points

#### **Interactive Prompts:**
```
Would you like to commit these changes now? (y/n): y
Enter commit message: Fixed Nutrition Database tab styling
```

#### **Example Output:**
```
🚀 Heart Portal Deployment
========================================
✅ Environment check passed - you're working locally
⚠️  You have uncommitted changes:
 M Nutrition-Database/templates/index.html
 M CLAUDE.md

Would you like to commit these changes now? (y/n): y
Enter commit message: Enhanced tabbed interface styling

✅ Changes committed successfully
✅ Pushing 1 new commit(s) to GitHub
✅ Deploying to Heart Portal server...
✅ All services started successfully!
✅ Deployment completed! 🎉
```

---

### `rollback.sh` - Production Rollback System

#### **All Commands:**
```bash
./scripts/rollback.sh                            # Quick rollback to previous version
./scripts/rollback.sh --force                    # Force rollback without safety checks
./scripts/rollback.sh --commit abc123            # Rollback to specific commit
./scripts/rollback.sh --list                     # List available rollback points
./scripts/rollback.sh --dry-run                  # Preview rollback without executing
```

#### **Examples:**
```bash
# Safe rollback with confirmation
./scripts/rollback.sh

# Emergency rollback (no confirmations)
./scripts/rollback.sh --force

# Rollback to specific commit
./scripts/rollback.sh --commit 3eb3b89

# List recent deployments available for rollback
./scripts/rollback.sh --list

# Test what would be rolled back
./scripts/rollback.sh --dry-run
```

---

### `deploy-staging-simple.sh` - Staging Deployment (PostgreSQL + Gunicorn)

#### **All Commands:**
```bash
./scripts/deploy-staging-simple.sh                    # Interactive deployment (default: postgres-migration)
BRANCH=main ./scripts/deploy-staging-simple.sh        # Deploy specific branch
./scripts/deploy-staging-simple.sh --help             # Show help and usage
```

#### **What It Does:**
1. **Environment Check** - Verifies you're working locally (not on server)
2. **Branch Selection** - Interactive branch selection or via BRANCH env var
3. **Uncommitted Changes** - Checks and optionally commits local changes
4. **GitHub Push** - Pushes selected branch to GitHub
5. **Server Deployment** - Pulls code on staging server via git
6. **Service Restart** - Restarts all 8 Gunicorn services
7. **Health Verification** - Confirms all services are active
8. **Database Preservation** - Keeps PostgreSQL databases and .env files intact

#### **What It PRESERVES:**
- ✅ **PostgreSQL databases** (no data loss)
- ✅ **`.env` files** (DATABASE_URL, STAGING_MODE, passwords)
- ✅ **`gunicorn_config.py` files** (worker configuration)
- ✅ **Server-specific configuration** (all preserved)

#### **Examples:**
```bash
# Interactive deployment (will prompt for branch)
./scripts/deploy-staging-simple.sh

# Deploy postgres-migration branch
BRANCH=postgres-migration ./scripts/deploy-staging-simple.sh

# Deploy main branch to staging
BRANCH=main ./scripts/deploy-staging-simple.sh

# View help
./scripts/deploy-staging-simple.sh --help
```

#### **Staging Environment:**
- **URL:** http://heartfailureportal.com:8081
- **Services:** 8 applications running with Gunicorn
- **Databases:** PostgreSQL (8 staging databases)
- **Nginx:** Port 8081 reverse proxy

#### **Staging Services:**
| Service | Port | Database | Systemd Service |
|---------|------|----------|-----------------|
| Main App | 3001 | blog | `heart-portal-staging-main` |
| Blog Manager | 5002 | blog | `heart-portal-staging-blog` |
| Nutrition Database | 5000 | nutrition | `heart-portal-staging-nutrition` |
| Food-Base | 5001 | food | `heart-portal-staging-food` |
| Sodium Tracker | 5003 | sodium | `heart-portal-staging-sodium` |
| Fluid Tracker | 5004 | fluid | `heart-portal-staging-fluid` |
| Weight Tracker | 5005 | weight | `heart-portal-staging-weight` |
| BP Monitor | 5006 | bp | `heart-portal-staging-bp` |

#### **Features:**
- ✅ Safe code updates (preserves data and configuration)
- ✅ Interactive branch selection
- ✅ Uncommitted change detection
- ✅ Automatic service restart
- ✅ Health verification after deployment
- ✅ PostgreSQL database preservation
- ✅ .env file preservation
- ✅ Detailed deployment feedback

#### **Important Notes:**
- 🚨 **DO NOT USE** `./scripts/deploy-staging.sh` (outdated, uses Flask dev server)
- 🚨 **DO NOT USE** `./scripts/cleanup-staging.sh` (will delete PostgreSQL data)
- ✅ **USE** `./scripts/deploy-staging-simple.sh` for current PostgreSQL + Gunicorn setup

---

## 🔒 SSL Management Scripts

### `setup-ssl.sh` - SSL Certificate Setup (One-time)

#### **Commands:**
```bash
# Run on server after initial deployment
sudo ./scripts/setup-ssl.sh                     # Setup Let's Encrypt certificates
sudo ./scripts/setup-ssl.sh --domain example.com # Setup for specific domain
```

### `renew-ssl.sh` - Certificate Renewal

#### **Commands:**
```bash
./scripts/renew-ssl.sh                          # Manual certificate renewal
./scripts/renew-ssl.sh --force                  # Force renewal
./scripts/renew-ssl.sh --dry-run                # Test renewal process
./scripts/renew-ssl.sh --auto                   # Setup automatic renewal
```

### `test-ssl.sh` - SSL Testing & Validation

#### **Commands:**
```bash
./scripts/test-ssl.sh                           # Comprehensive SSL testing
./scripts/test-ssl.sh --quick                   # Quick SSL validation
./scripts/test-ssl.sh --external                # Test from external services
```

---

## 💻 Local Development Scripts

### `restart-clean.sh` - Clean Local Application Restart
**Updated:** Now uses shared .env configuration

#### **Commands:**
```bash
./scripts/restart-clean.sh                       # Stop all processes and restart using .env
```

#### **What It Does:**
1. **Process Cleanup** - Kills all existing Python Flask processes
2. **Clean Start** - Waits for complete process termination
3. **Environment Loading** - Uses shared `.env` file for configuration
4. **Service Startup** - Starts all 7 Flask applications using centralized environment
5. **Status Report** - Shows PIDs and access information

#### **Features:**
- ✅ Uses shared `.env` file (no hardcoded environment variables)
- ✅ Dynamic path resolution (works from any directory)
- ✅ Clean process termination before restart
- ✅ Consistent environment across all applications

#### **Example Output:**
```
🧹 Stopping all Flask applications...
🚀 Starting all applications using shared .env configuration...
▶️ Starting Main App (port 3000)...
▶️ Starting Nutrition Database (port 5000)...
...
✅ All applications started with PIDs:
   Main App: 46709
   Nutrition: 46710
🌐 Access through: http://localhost:8080
```

---

### `start-all-apps.sh` - Local Development Server Startup
**Updated:** Now uses shared .env configuration

#### **Commands:**
```bash
./scripts/start-all-apps.sh                     # Start all Flask apps using .env config
```

#### **What It Does:**
1. **Process Management** - Cleans up existing application processes
2. **Environment Loading** - Uses shared `.env` file automatically
3. **Service Startup** - Starts all Heart Portal applications
4. **Status Reporting** - Confirms successful startup with access URLs

#### **Applications Started:**
- Main App (port 3000)
- Blog Manager (port 5002)
- Nutrition Database (port 5000)
- Food Base (port 5001)
- Sodium Tracker (port 5003)
- Fluid Tracker (port 5004)
- Weight Tracker (port 5005)
- BP Monitor (port 5006)

#### **Features:**
- ✅ Uses shared `.env` file for `REVERSE_PROXY_MODE=true`
- ✅ Automatic process cleanup before starting
- ✅ Dynamic project root detection
- ✅ No hardcoded paths or environment variables

---

### `start-proxy.sh` - Nginx Reverse Proxy Startup
**Updated:** Simplified for nginx-only operation

#### **Commands:**
```bash
./scripts/start-proxy.sh                        # Start nginx reverse proxy on port 8080
```

#### **What It Does:**
1. **Nginx Validation** - Checks if nginx is installed
2. **Process Cleanup** - Stops existing nginx processes
3. **Proxy Start** - Starts nginx with Heart Portal configuration
4. **URL Guide** - Shows all application access URLs

#### **Features:**
- ✅ No redundant environment variables (Flask apps handle their own .env)
- ✅ Clean nginx-only operation
- ✅ Comprehensive URL mapping guide
- ✅ Dependency checking (nginx installation)

#### **Access URLs:**
```
📍 Access your applications at:
   🏠 Main App:         http://localhost:8080/
   📝 Blog:            http://localhost:8080/blog/
   🔍 Nutrition:       http://localhost:8080/nutrition/
   🍎 Food Storage:    http://localhost:8080/food/
   🧂 Sodium Tracker:  http://localhost:8080/sodium/
   💧 Fluid Tracker:   http://localhost:8080/fluid/
   ⚖️ Weight Tracker:  http://localhost:8080/weight/
```

---

## 🗄️ Data Management Scripts

### `download-database.sh` - Database Synchronization

#### **Commands:**
```bash
./scripts/download-database.sh                  # Download all production databases
./scripts/download-database.sh --app nutrition  # Download specific app database
./scripts/download-database.sh --backup         # Create backup before download
```

#### **Examples:**
```bash
# Download all databases from production
./scripts/download-database.sh

# Download only nutrition database
./scripts/download-database.sh --app nutrition

# Download with local backup first
./scripts/download-database.sh --backup
```

---

## 🌐 Connection & Setup Scripts

### `connect-server.sh` - Server Connection

#### **Commands:**
```bash
./scripts/connect-server.sh                     # Quick SSH to production server
./scripts/connect-server.sh --tunnel            # SSH with port forwarding
```

### `dev-check.sh` - Environment Verification

#### **Commands:**
```bash
./scripts/dev-check.sh                          # Verify local development environment
./scripts/dev-check.sh --verbose                # Detailed environment check
```

### `setup-server.sh` - Server Setup (Initial)

#### **Commands:**
```bash
# Run during initial server setup only
./scripts/setup-server.sh                       # Configure production server
./scripts/setup-server.sh --full                # Complete server setup with dependencies
```

---

## 💡 Usage Patterns & Workflows

### 🔄 **Daily Development Workflow**
```bash
# 1. Verify you're working locally
./scripts/dev-check.sh

# 2. Make your code changes
# ... edit files ...

# 3a. Deploy to staging for testing (PostgreSQL + Gunicorn)
./scripts/deploy-staging-simple.sh

# 3b. OR deploy directly to production (after staging tests pass)
./scripts/deploy.sh

# 4. Monitor deployment success
./scripts/monitor.sh all
```

### 💻 **Local Development Workflow**
```bash
# 1. Start local development environment (all Flask apps)
./scripts/restart-clean.sh

# 2. Start nginx reverse proxy for testing
./scripts/start-proxy.sh

# 3. Access applications through reverse proxy
# http://localhost:8080 (main navigation)
# http://localhost:8080/blog/ (blog manager)
# http://localhost:8080/nutrition/ (nutrition database)
# etc.

# 4. Stop all services when done
pkill -f "python.*app.py"
pkill nginx
```

### 🚨 **Troubleshooting Workflow**
```bash
# 1. Quick diagnostic of all systems
./scripts/troubleshoot.sh full

# 2. Fix any identified issues automatically
./scripts/troubleshoot.sh full --fix

# 3. Verify all services are healthy
./scripts/monitor.sh all

# 4. If problems persist, rollback
./scripts/rollback.sh
```

### 🔧 **Service Management Workflow**
```bash
# Check production status
./scripts/manage-services.sh status

# Check staging status
./scripts/manage-services.sh status --staging

# Restart problematic production service
./scripts/manage-services.sh restart main

# Restart all staging services after deployment
./scripts/manage-services.sh restart --staging

# Fix main app port conflicts (production)
./scripts/manage-services.sh update

# Start continuous monitoring
./scripts/monitor.sh continuous
```

### 🔒 **SSL Certificate Workflow**
```bash
# Test current SSL status
./scripts/test-ssl.sh

# Renew certificates if needed
./scripts/renew-ssl.sh

# Verify renewal worked
./scripts/test-ssl.sh --quick
```

---

## 🏗️ Service Architecture

### **Heart Portal Services**
| Service | Port | Description | Systemd Service |
|---------|------|-------------|-----------------|
| **Main App** | 3000 | Landing page and navigation | `heart-portal-main` |
| **Nutrition Database** | 5000 | USDA API interface | `heart-portal-nutrition` |
| **Food-Base** | 5001 | Personal food storage | `heart-portal-food` |
| **Blog Manager** | 5002 | Blog management system | `heart-portal-blog` |
| **Sodium Tracker** | 5003 | Daily sodium intake tracking | `heart-portal-sodium` |
| **Fluid Tracker** | 5004 | Daily fluid intake monitoring | `heart-portal-fluid` |
| **Weight Tracker** | 5005 | Daily weight tracking | `heart-portal-weight` |
| **BP Monitor** | 5006 | Blood pressure monitoring | `heart-portal-bp` |
| **Nginx** | 80, 443 | Reverse proxy and SSL | `nginx` |

### **Service Dependencies**
```
nginx (80/443) → SSL Termination & Reverse Proxy
    ├── → heart-portal-main (3000)        → Landing & Navigation
    ├── → heart-portal-nutrition (5000)   → USDA Food Data
    ├── → heart-portal-food (5001)        → Personal Food Storage
    ├── → heart-portal-blog (5002)        → Blog System
    ├── → heart-portal-sodium (5003)      → Sodium Tracking
    ├── → heart-portal-fluid (5004)       → Fluid Tracking
    ├── → heart-portal-weight (5005)      → Weight Tracking
    └── → heart-portal-bp (5006)          → Blood Pressure Monitoring
```

### **Production URLs**
- **Main Site:** https://heartfailureportal.com
- **Nutrition Database:** https://heartfailureportal.com/nutrition-database/
- **Food-Base:** https://heartfailureportal.com/food-base/
- **Blog Manager:** https://heartfailureportal.com/blog-manager/
- **Sodium Tracker:** https://heartfailureportal.com/sodium-tracker/
- **Fluid Tracker:** https://heartfailureportal.com/fluid-tracker/
- **Weight Tracker:** https://heartfailureportal.com/weight-tracker/

---

## 🔧 Common Issues & Solutions

### **Port 3000 Conflicts**
```bash
# Automatic diagnosis and fix
./scripts/troubleshoot.sh port --fix

# Manual resolution
./scripts/manage-services.sh update
```

### **Service Startup Failures**
```bash
# Check specific service status
./scripts/manage-services.sh status [service]

# Auto-repair service issues
./scripts/troubleshoot.sh services --fix

# Manual restart
./scripts/manage-services.sh restart [service]
```

### **SSL Certificate Issues**
```bash
# Validate current SSL setup
./scripts/test-ssl.sh

# Force certificate renewal
./scripts/renew-ssl.sh --force

# Full SSL diagnostic and repair
./scripts/troubleshoot.sh ssl --fix
```

### **Deployment Problems**
```bash
# Quick rollback to previous version
./scripts/rollback.sh

# Full system diagnostic
./scripts/troubleshoot.sh full

# Emergency force rollback
./scripts/rollback.sh --force
```

### **Database Connectivity Issues**
```bash
# Test database connections
./scripts/troubleshoot.sh database

# Download fresh databases from production
./scripts/download-database.sh --backup
```

---

## 📋 Quick Reference Commands

### **Most Frequent Commands**
```bash
# Deploy changes to production
./scripts/deploy.sh

# Check all service status
./scripts/monitor.sh all

# Fix port conflicts automatically
./scripts/troubleshoot.sh port --fix

# Restart all services
./scripts/manage-services.sh restart

# Connect to production server
./scripts/connect-server.sh

# Emergency rollback
./scripts/rollback.sh --force
```

### **Emergency Procedures**
```bash
# Complete service failure recovery
./scripts/troubleshoot.sh full --fix
./scripts/manage-services.sh restart
./scripts/monitor.sh all

# SSL certificate emergency renewal
./scripts/renew-ssl.sh --force
./scripts/test-ssl.sh

# Bad deployment recovery
./scripts/rollback.sh --force
./scripts/monitor.sh all

# Database corruption recovery
./scripts/download-database.sh --backup
./scripts/manage-services.sh restart
```

---

## 📊 Script Consolidation Summary

### **✅ Scripts Consolidated (7 removed, 37% reduction)**
| Old Scripts (Removed) | New Consolidated Script |
|----------------------|------------------------|
| `start-system.sh` | **`manage-services.sh`** |
| `stop-system.sh` | **`manage-services.sh`** |
| `status-system.sh` | **`manage-services.sh`** |
| `update-main-service.sh` | **`manage-services.sh`** |
| `monitor-services.sh` | **`monitor.sh`** |
| `monitor-main-app.sh` | **`monitor.sh`** |
| `diagnose-port-3000.sh` | **`troubleshoot.sh`** |
| `safe-server-test.sh` | **`troubleshoot.sh`** |
| `test-solution.sh` | **`troubleshoot.sh`** |

### **📈 Benefits Achieved**
- ✅ **Reduced complexity:** 19 → 12 scripts (-37%)
- ✅ **Eliminated overlaps:** Clear functional boundaries
- ✅ **Better organization:** Logical script groupings
- ✅ **Enhanced features:** More comprehensive functionality per script
- ✅ **Easier maintenance:** Fewer files to manage and update
- ✅ **Improved usability:** Clearer naming and consistent usage patterns
- ✅ **Better documentation:** Comprehensive help and examples
- ✅ **Enhanced error handling:** Better diagnostics and recovery

---

## 🎯 Best Practices

### **Development Workflow**
1. Always run `./scripts/dev-check.sh` before making changes
2. Use `./scripts/deploy.sh` for all deployments (handles git automatically)
3. Monitor deployments with `./scripts/monitor.sh all`
4. Keep rollback ready with `./scripts/rollback.sh` if issues arise

### **Environment Configuration**
1. **Single Source of Truth**: All environment variables are managed through the shared `.env` file in the project root
2. **No Script Overrides**: Local development scripts (`restart-clean.sh`, `start-all-apps.sh`) rely entirely on `.env` file
3. **Consistent Configuration**: `REVERSE_PROXY_MODE=true` is set in `.env` to ensure proper navigation URLs
4. **No Hardcoded Values**: All scripts use dynamic path resolution and environment loading

### **Troubleshooting**
1. Start with `./scripts/troubleshoot.sh quick` for fast diagnosis
2. Use `--fix` flags for automatic repair when possible
3. Monitor continuously with `./scripts/monitor.sh continuous` during issues
4. Document issues and solutions for future reference

### **Service Management**
1. Use bulk operations (`all`) when possible for consistency
2. Check status before making changes
3. Restart services individually when debugging specific issues
4. Update main service configuration when experiencing port conflicts

### **Security & SSL**
1. Test SSL regularly with `./scripts/test-ssl.sh`
2. Monitor certificate expiration dates
3. Use `--dry-run` flags to test changes before applying
4. Keep SSL configurations backed up

This comprehensive documentation provides all the information needed to effectively manage the Heart Portal infrastructure using the consolidated script system.