# Heart Portal Scripts Documentation

## Overview

This document describes the consolidated script system for Heart Portal management. The scripts have been reorganized to eliminate overlaps and provide clearer functionality.

**Total Scripts: 12** (reduced from 19 - eliminated 7 duplicate/overlapping scripts)

## Script Organization

### 🚀 **Deployment & Environment**
- `deploy.sh` - Main deployment workflow (push to GitHub + server deployment)
- `rollback.sh` - Production rollback system with safety checks
- `dev-check.sh` - Environment verification (local vs server)
- `connect-server.sh` - Simple SSH connection to production server

### 🔧 **Service Management**
- `manage-services.sh` - **[NEW]** Complete service lifecycle management
- `monitor.sh` - **[NEW]** Service monitoring and health checks
- `troubleshoot.sh` - **[NEW]** Comprehensive diagnostic and repair tools

### 🔒 **SSL & Security**
- `setup-ssl.sh` - One-time SSL certificate setup
- `renew-ssl.sh` - SSL certificate renewal management
- `test-ssl.sh` - SSL/HTTPS testing and validation

### 🗄️ **Data Management**
- `download-database.sh` - Sync production database to local environment

### ⚙️ **Server Setup**
- `setup-server.sh` - Initial server configuration and setup

---

## New Consolidated Scripts

### 🔧 `manage-services.sh` - Service Management
**Replaces:** `start-system.sh`, `stop-system.sh`, `status-system.sh`, `update-main-service.sh`

```bash
# Service control
./scripts/manage-services.sh start               # Start all services
./scripts/manage-services.sh stop                # Stop all services
./scripts/manage-services.sh restart             # Restart all services
./scripts/manage-services.sh status              # Show all service status

# Individual service control
./scripts/manage-services.sh start main          # Start main app only
./scripts/manage-services.sh restart nutrition   # Restart nutrition service
./scripts/manage-services.sh status blog         # Check blog service status

# Service updates
./scripts/manage-services.sh update              # Update main service (fix port conflicts)
```

**Features:**
- Unified service lifecycle management
- Individual or bulk service operations
- Automatic port conflict resolution for main app
- Local/remote execution detection
- Health verification after operations

### 📊 `monitor.sh` - Service Monitoring
**Replaces:** `monitor-services.sh`, `monitor-main-app.sh`

```bash
# Quick status checks
./scripts/monitor.sh all                         # Status of all services
./scripts/monitor.sh main                        # Detailed main app status

# Continuous monitoring
./scripts/monitor.sh continuous                  # Start continuous monitoring with auto-restart

# Execution modes
./scripts/monitor.sh all --local                 # Monitor from local machine
./scripts/monitor.sh all --remote                # Monitor directly on server
```

**Features:**
- Health scoring system (0-100%)
- Automatic service restart on failure
- SSL certificate monitoring
- Response time measurements
- Memory usage tracking
- Configurable monitoring intervals

### 🔍 `troubleshoot.sh` - Diagnostic & Repair
**Replaces:** `diagnose-port-3000.sh`, `safe-server-test.sh`, `test-solution.sh`

```bash
# Specific diagnostics
./scripts/troubleshoot.sh port                   # Port 3000 conflict diagnosis
./scripts/troubleshoot.sh services               # Service health testing
./scripts/troubleshoot.sh ssl                    # SSL/HTTPS validation
./scripts/troubleshoot.sh network                # Network connectivity tests
./scripts/troubleshoot.sh system                 # System health check

# Comprehensive testing
./scripts/troubleshoot.sh full                   # Complete system diagnostic

# Auto-repair mode
./scripts/troubleshoot.sh port --fix             # Diagnose and fix port issues
./scripts/troubleshoot.sh services --fix         # Test and repair services
```

**Features:**
- Port conflict detection and resolution
- Service health validation
- SSL certificate verification
- Network connectivity testing
- System resource monitoring
- Automatic repair capabilities
- Detailed diagnostic reporting

---

## Core Scripts (Unchanged)

### 🚀 **Deployment Scripts**

#### `deploy.sh` - Main Deployment
```bash
./scripts/deploy.sh                              # Deploy all changes to production
```
- Commits changes to git
- Pushes to GitHub repository
- Syncs files to production server
- Restarts affected services
- Runs health checks
- Creates recovery tags

#### `rollback.sh` - Production Rollback
```bash
./scripts/rollback.sh                            # Quick rollback to previous version
./scripts/rollback.sh --force                    # Force rollback without safety checks
./scripts/rollback.sh --commit abc123            # Rollback to specific commit
```
- Git-based rollback system
- Automatic service restart
- Health verification
- Safety checks and confirmations

#### `dev-check.sh` - Environment Verification
```bash
./scripts/dev-check.sh                           # Verify local development environment
```
- Prevents accidental server-side editing
- Validates environment setup
- Checks required dependencies

### 🔒 **SSL Management**

#### `setup-ssl.sh` - SSL Setup (One-time)
```bash
# Run on server after deployment
sudo ./scripts/setup-ssl.sh                     # Setup Let's Encrypt certificates
```
- Installs SSL certificates
- Configures nginx for HTTPS
- Sets up automatic renewal

#### `renew-ssl.sh` - Certificate Renewal
```bash
./scripts/renew-ssl.sh                          # Manual certificate renewal
./scripts/renew-ssl.sh --force                  # Force renewal
```
- Renews Let's Encrypt certificates
- Tests certificate validity
- Reloads nginx configuration

#### `test-ssl.sh` - SSL Testing
```bash
./scripts/test-ssl.sh                           # Comprehensive SSL testing
```
- Certificate validation
- HTTPS connectivity testing
- Security configuration verification

### 🗄️ **Database Management**

#### `download-database.sh` - Database Sync
```bash
./scripts/download-database.sh                  # Download production databases
```
- Downloads all application databases
- Preserves data integrity
- Creates local backups

### 🌐 **Connection & Setup**

#### `connect-server.sh` - Server Connection
```bash
./scripts/connect-server.sh                     # Quick SSH to production server
```
- Simple SSH connection helper
- Uses correct SSH keys and settings

#### `setup-server.sh` - Server Setup
```bash
# Run during initial server setup
./scripts/setup-server.sh                       # Configure production server
```
- Initial server configuration
- Service setup and configuration
- Dependency installation

---

## Usage Patterns

### 🔄 **Daily Development Workflow**
```bash
# 1. Check environment
./scripts/dev-check.sh

# 2. Make local changes
# ... edit code ...

# 3. Deploy to production
./scripts/deploy.sh

# 4. Monitor deployment
./scripts/monitor.sh all
```

### 🚨 **Troubleshooting Workflow**
```bash
# 1. Quick diagnostic
./scripts/troubleshoot.sh full

# 2. Fix specific issues
./scripts/troubleshoot.sh port --fix

# 3. Verify services
./scripts/monitor.sh all

# 4. If problems persist
./scripts/rollback.sh
```

### 🔧 **Service Management Workflow**
```bash
# Check status
./scripts/manage-services.sh status

# Restart problematic service
./scripts/manage-services.sh restart main

# Update main service configuration
./scripts/manage-services.sh update

# Monitor continuously
./scripts/monitor.sh continuous
```

---

## Service Definitions

### Heart Portal Services
- **heart-portal-main** (port 3000) - Landing page and navigation
- **heart-portal-nutrition** (port 5000) - USDA API interface
- **heart-portal-food** (port 5001) - Personal food storage
- **heart-portal-blog** (port 5002) - Blog management system
- **nginx** (ports 80, 443) - Reverse proxy and SSL termination

### Service Dependencies
```
nginx (80/443)
    ├── → heart-portal-main (3000)
    ├── → heart-portal-nutrition (5000)
    ├── → heart-portal-food (5001)
    └── → heart-portal-blog (5002)
```

---

## Error Handling & Logging

### Log Locations
- **Monitoring logs:** `/var/log/heart-portal-monitoring.log`
- **Alert logs:** `/var/log/heart-portal-alerts.log`
- **SSL renewal logs:** `/var/log/heart-portal-ssl-renewal.log`

### Common Issues & Solutions

#### Port 3000 Conflicts
```bash
./scripts/troubleshoot.sh port --fix             # Automatic resolution
```

#### Service Startup Failures
```bash
./scripts/manage-services.sh status              # Check status
./scripts/troubleshoot.sh services --fix         # Auto-repair
```

#### SSL Certificate Issues
```bash
./scripts/test-ssl.sh                           # Validate SSL
./scripts/renew-ssl.sh --force                  # Force renewal
```

#### Deployment Problems
```bash
./scripts/rollback.sh                           # Rollback to previous version
./scripts/troubleshoot.sh full                  # Full diagnostic
```

---

## Script Consolidation Summary

### ✅ **Scripts Consolidated (9 removed)**
- `start-system.sh` → **`manage-services.sh`**
- `stop-system.sh` → **`manage-services.sh`**
- `status-system.sh` → **`manage-services.sh`**
- `update-main-service.sh` → **`manage-services.sh`**
- `monitor-services.sh` → **`monitor.sh`**
- `monitor-main-app.sh` → **`monitor.sh`**
- `diagnose-port-3000.sh` → **`troubleshoot.sh`**
- `safe-server-test.sh` → **`troubleshoot.sh`**
- `test-solution.sh` → **`troubleshoot.sh`**

### 📈 **Benefits**
- **Reduced complexity:** 19 → 12 scripts (-37%)
- **Eliminated overlaps:** Clear functional boundaries
- **Better organization:** Logical groupings
- **Enhanced features:** More comprehensive functionality
- **Easier maintenance:** Fewer files to manage
- **Improved usability:** Clearer naming and usage patterns

---

## Quick Reference

### Most Common Commands
```bash
# Deploy changes
./scripts/deploy.sh

# Check all services
./scripts/monitor.sh all

# Fix port conflicts
./scripts/troubleshoot.sh port --fix

# Restart services
./scripts/manage-services.sh restart

# Connect to server
./scripts/connect-server.sh

# Emergency rollback
./scripts/rollback.sh
```

### Emergency Procedures
```bash
# Complete service failure
./scripts/troubleshoot.sh full --fix
./scripts/manage-services.sh restart
./scripts/monitor.sh all

# SSL certificate expired
./scripts/renew-ssl.sh --force
./scripts/test-ssl.sh

# Deployment went wrong
./scripts/rollback.sh --force
```