# Heart Portal Scripts Reference

## Deployment & Connection Scripts

### `deploy.sh`
**Target:** Production Server
**Description:** Main deployment script that pushes changes to GitHub and triggers server-side deployment. Handles git checks, dependency updates, and service restarts.

### `rollback.sh`
**Target:** Production Server
**Description:** Production rollback script that reverts server to previous version. Includes safety checks, creates recovery tags, and handles service restarts. Can run locally via SSH or directly on server.

### `connect-server.sh`  
**Target:** Production Server  
**Description:** Quick SSH connection helper to production server. Automatically navigates to project directory.

### `dev-check.sh`
**Target:** Local Development  
**Description:** Verifies local development environment, checks directory, git status, and required files. Prevents accidental server-side development.

## SSL Management Scripts

### `setup-ssl.sh`
**Target:** Production Server  
**Description:** One-time SSL setup with Let's Encrypt certificates. Installs Nginx, configures reverse proxy, obtains SSL certificates, and sets up auto-renewal.

### `renew-ssl.sh`
**Target:** Production Server  
**Description:** Manual SSL certificate renewal with backup and verification. Includes dry-run testing and service reload.

### `test-ssl.sh`
**Target:** Production Server  
**Description:** Comprehensive SSL/HTTPS testing for all endpoints. Checks certificate validity, security headers, and performance metrics.

## System Management Scripts

### `start-system.sh`
**Target:** Local Development  
**Description:** Starts all Heart Portal components locally in correct order. Creates virtual environments and manages background processes.

### `status-system.sh`
**Target:** Local Development  
**Description:** Shows status of all local components, checks ports, and provides quick management commands.

### `stop-system.sh`
**Target:** Local Development  
**Description:** Gracefully stops all local components and cleans up PID files and logs.

### `setup-server.sh`
**Target:** Production Server  
**Description:** Initial server setup script. Creates virtual environments, installs systemd services, sets permissions, and starts all services.

## Database & Monitoring Scripts

### `download-database.sh`
**Target:** Local Development  
**Description:** Downloads production database to local environment with backup and verification. One-way sync from production to local.

### `monitor-services.sh`
**Target:** Local → Production Server
**Description:** Health monitoring for all services including Nginx and SSL certificates. Can run locally via SSH to monitor remote server. Provides comprehensive system status check.

## Script Usage Summary

| Script | Environment | Purpose |
|--------|-------------|---------|
| `deploy.sh` | Local → Server | Deploy changes to production |
| `rollback.sh` | Local → Server | Rollback production to previous version |
| `connect-server.sh` | Local | SSH to production server |
| `dev-check.sh` | Local | Verify development environment |
| `setup-ssl.sh` | Server | Initial SSL certificate setup |
| `renew-ssl.sh` | Server | Renew SSL certificates |
| `test-ssl.sh` | Server | Test SSL/HTTPS functionality |
| `start-system.sh` | Local | Start all services locally |
| `status-system.sh` | Local | Check local service status |
| `stop-system.sh` | Local | Stop all local services |
| `setup-server.sh` | Server | Initial server configuration |
| `download-database.sh` | Local | Sync database from production |
| `monitor-services.sh` | Local → Server | Monitor production health |

## Quick Reference Commands

```bash
# Local Development
./dev-check.sh              # Check environment
./start-system.sh           # Start all services
./status-system.sh          # Check service status
./stop-system.sh            # Stop all services
./download-database.sh      # Get production database

# Deployment & Rollback (Local → Server)
./deploy.sh                 # Deploy to production
./monitor-services.sh       # Check production health
./rollback.sh               # Rollback production server
./rollback.sh --force       # Force rollback without checks
./rollback.sh --commit abc123  # Rollback to specific commit

# Production Server (via SSH)
./connect-server.sh         # SSH to server
sudo ./setup-server.sh     # Initial server setup
sudo ./setup-ssl.sh        # Setup SSL certificates
sudo ./renew-ssl.sh         # Renew SSL certificates
./test-ssl.sh              # Test SSL functionality
```