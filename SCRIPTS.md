# Heart Portal Scripts Reference

## Deployment & Connection Scripts

### `scripts/deploy.sh`
**Target:** Production Server
**Description:** Main deployment script that pushes changes to GitHub and triggers server-side deployment. Handles git checks, dependency updates, and service restarts.

### `scripts/rollback.sh`
**Target:** Production Server
**Description:** Production rollback script that reverts server to previous version. Includes safety checks, creates recovery tags, and handles service restarts. Can run locally via SSH or directly on server.

### `scripts/connect-server.sh`  
**Target:** Production Server  
**Description:** Quick SSH connection helper to production server. Automatically navigates to project directory.

### `scripts/dev-check.sh`
**Target:** Local Development  
**Description:** Verifies local development environment, checks directory, git status, and required files. Prevents accidental server-side development.

## SSL Management Scripts

### `scripts/setup-ssl.sh`
**Target:** Production Server  
**Description:** One-time SSL setup with Let's Encrypt certificates. Installs Nginx, configures reverse proxy, obtains SSL certificates, and sets up auto-renewal.

### `scripts/renew-ssl.sh`
**Target:** Production Server  
**Description:** Manual SSL certificate renewal with backup and verification. Includes dry-run testing and service reload.

### `scripts/test-ssl.sh`
**Target:** Production Server  
**Description:** Comprehensive SSL/HTTPS testing for all endpoints. Checks certificate validity, security headers, and performance metrics.

## System Management Scripts

### `scripts/start-system.sh`
**Target:** Local Development  
**Description:** Starts all Heart Portal components locally in correct order. Creates virtual environments and manages background processes.

### `scripts/status-system.sh`
**Target:** Local Development  
**Description:** Shows status of all local components, checks ports, and provides quick management commands.

### `scripts/stop-system.sh`
**Target:** Local Development  
**Description:** Gracefully stops all local components and cleans up PID files and logs.

### `scripts/setup-server.sh`
**Target:** Production Server  
**Description:** Initial server setup script. Creates virtual environments, installs systemd services, sets permissions, and starts all services.

## Database & Monitoring Scripts

### `scripts/download-database.sh`
**Target:** Local Development  
**Description:** Downloads production database to local environment with backup and verification. One-way sync from production to local.

### `scripts/monitor-services.sh`
**Target:** Local → Production Server
**Description:** Health monitoring for all services including Nginx and SSL certificates. Can run locally via SSH to monitor remote server. Provides comprehensive system status check.

## Script Usage Summary

| Script | Environment | Purpose |
|--------|-------------|---------|
| `scripts/deploy.sh` | Local → Server | Deploy changes to production |
| `scripts/rollback.sh` | Local → Server | Rollback production to previous version |
| `scripts/connect-server.sh` | Local | SSH to production server |
| `scripts/dev-check.sh` | Local | Verify development environment |
| `scripts/setup-ssl.sh` | Server | Initial SSL certificate setup |
| `scripts/renew-ssl.sh` | Server | Renew SSL certificates |
| `scripts/test-ssl.sh` | Server | Test SSL/HTTPS functionality |
| `scripts/start-system.sh` | Local | Start all services locally |
| `scripts/status-system.sh` | Local | Check local service status |
| `scripts/stop-system.sh` | Local | Stop all local services |
| `scripts/setup-server.sh` | Server | Initial server configuration |
| `scripts/download-database.sh` | Local | Sync database from production |
| `scripts/monitor-services.sh` | Local → Server | Monitor production health |

## Quick Reference Commands

```bash
# Local Development
./scripts/dev-check.sh              # Check environment
./scripts/start-system.sh           # Start all services
./scripts/status-system.sh          # Check service status
./scripts/stop-system.sh            # Stop all services
./scripts/download-database.sh      # Get production database

# Deployment & Rollback (Local → Server)
./scripts/deploy.sh                 # Deploy to production
./scripts/monitor-services.sh       # Check production health
./scripts/rollback.sh               # Rollback production server
./scripts/rollback.sh --force       # Force rollback without checks
./scripts/rollback.sh --commit abc123  # Rollback to specific commit

# Production Server (via SSH)
./scripts/connect-server.sh         # SSH to server
sudo ./scripts/setup-server.sh     # Initial server setup
sudo ./scripts/setup-ssl.sh        # Setup SSL certificates
sudo ./scripts/renew-ssl.sh         # Renew SSL certificates
./scripts/test-ssl.sh              # Test SSL functionality
```