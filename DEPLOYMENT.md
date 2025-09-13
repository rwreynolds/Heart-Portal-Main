# Heart Portal Deployment Guide

This document explains how to deploy changes to the Heart Portal production server.

## Quick Deployment

For most deployments, simply run:

```bash
./deploy.sh
```

This will automatically:
1. ✅ Check for uncommitted changes
2. ✅ Push commits to GitHub
3. ✅ Deploy to production server (CODE ONLY)
4. ✅ Restart all services
5. ✅ Verify deployment health
6. ✅ **Preserve production database** (no data loss)

## Production Rollback

If deployment causes issues, quickly rollback:

```bash
./rollback.sh              # Rollback to previous version
./rollback.sh --force      # Force rollback without safety checks
./rollback.sh --commit abc123  # Rollback to specific commit
```

This will automatically:
1. ✅ Check current service health (unless --force)
2. ✅ Create recovery tag for easy restoration
3. ✅ Stop all services
4. ✅ Checkout previous/target commit
5. ✅ Reinstall dependencies
6. ✅ Restart all services
7. ✅ Verify rollback success

## Database Management

### Download Production Database
To sync the production database to your local environment:

```bash
./download-database.sh
```

This will:
- ✅ Backup your current local database
- ✅ Download the production database 
- ✅ Replace your local database
- ✅ Show food counts and statistics

### Important Database Rules
- 🔒 **Local database changes NEVER deploy to production**
- 🔒 **Production database is preserved during deployments**
- 📥 **You can download production data anytime**
- 🏠 **Local data stays local for testing**

## Development Workflow

### 1. Make Changes Locally
- Edit files in your local VSCode project
- Test with local development servers:
  ```bash
  # Terminal 1: Main App
  cd main-app && python main_app.py
  
  # Terminal 2: Nutrition Database  
  cd Nutrition-Database && python app.py
  
  # Terminal 3: Food-Base
  cd Food-Base && python app.py
  
  # Terminal 4: Blog Manager
  cd Blog-Manager && python app.py
  ```

### 2. Commit Changes
```bash
git add .
git commit -m "Description of your changes"
```

### 3. Deploy to Production
```bash
./deploy.sh
```

### 4. Test Deployment
```bash
./monitor-services.sh      # Check all services are healthy
```

### 5. If Issues Found - Rollback
```bash
./rollback.sh              # Quick rollback to previous version
```

## Manual Deployment (if needed)

If you need to deploy manually:

```bash
# 1. Push to GitHub
git push origin main

# 2. Deploy on server
ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161
cd /opt/heart-portal
./deploy.sh server
```

## Production URLs

After deployment, your Heart Portal will be available at:

- **🌐 Main Site**: https://heartfailureportal.com
- **🔍 Nutrition Database**: https://heartfailureportal.com/nutrition-database/
- **🍎 Food-Base**: https://heartfailureportal.com/food-base/
- **📝 Blog Manager**: https://heartfailureportal.com/blog-manager/

## Complete Deploy → Test → Rollback Workflow

### Normal Deployment Flow
```bash
# 1. Make changes locally, test, commit
git add . && git commit -m "Your changes"

# 2. Deploy to production
./deploy.sh

# 3. Verify deployment
./monitor-services.sh

# 4. If everything looks good, you're done! ✅
```

### Emergency Rollback Flow
```bash
# If deployment causes issues:
./rollback.sh              # Quick rollback

# Fix issues locally while production runs on previous version
# Then redeploy when ready:
./deploy.sh
```

### Recovery from Failed Rollback
If rollback fails, manual recovery options:
```bash
ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161
cd /opt/heart-portal
git tag                     # Find rollback tag
git checkout rollback-from-<hash>-<timestamp>
sudo systemctl restart heart-portal-*
```

## Troubleshooting

### Check Service Status
```bash
./monitor-services.sh       # Local command to check remote server
# OR manually:
ssh -i /Users/mrrobot/.ssh/id_ed25519 heartportal@129.212.181.161
sudo systemctl status heart-portal-*
```

### Check Service Logs
```bash
# All services logs
sudo journalctl -u heart-portal-* --lines=50

# Individual service logs
sudo journalctl -u heart-portal-main --lines=20
sudo journalctl -u heart-portal-nutrition --lines=20
sudo journalctl -u heart-portal-food --lines=20
sudo journalctl -u heart-portal-blog --lines=20
```

### Restart Individual Services
```bash
# Restart all services
sudo systemctl restart heart-portal-*

# Restart individual services
sudo systemctl restart heart-portal-main
sudo systemctl restart heart-portal-nutrition
sudo systemctl restart heart-portal-food
sudo systemctl restart heart-portal-blog
```

## Server Details

- **Server**: heartfailureportal.com (129.212.181.161)
- **Project Directory**: `/opt/heart-portal`
- **User**: `heartportal`
- **Services**: 
  - nginx (port 80/443 - HTTPS/SSL enabled)
  - heart-portal-main (port 3000)
  - heart-portal-nutrition (port 5000) 
  - heart-portal-food (port 5001)
  - heart-portal-blog (port 5002)

## Environment Variables

The production server uses:
- **USDA_API_KEY**: Set in `/opt/heart-portal/Nutrition-Database/.env`
- All other environment variables are configured automatically
- SSL certificates managed automatically via Let's Encrypt

## Best Practices

1. ✅ **Always test locally first** before deploying
2. ✅ **Commit meaningful messages** that describe your changes  
3. ✅ **Deploy frequently** with small changes rather than large batches
4. ✅ **Check the live site** after deployment to verify everything works
5. ✅ **Monitor logs** if you notice any issues

## Need Help?

If you encounter any deployment issues:
1. Check the deployment logs on the server
2. Verify all services are running with `ps aux | grep python`
3. Test endpoints manually with `curl`
4. Check nginx configuration with `nginx -t`

The deployment scripts include comprehensive error checking and health verification to catch most issues automatically.