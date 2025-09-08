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
  
  # Terminal 2: API Manager  
  cd API-manager && python app.py
  
  # Terminal 3: Food-Base
  cd Food-Base && python app.py
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

## Manual Deployment (if needed)

If you need to deploy manually:

```bash
# 1. Push to GitHub
git push origin main

# 2. Deploy on server
ssh -i ./Food-Base/heart_portal_key root@129.212.181.161
cd /opt/heart-portal
./deploy.sh
```

## Production URLs

After deployment, your Heart Portal will be available at:

- **🌐 Main Site**: https://heartfailureportal.com
- **🔍 API Manager**: https://heartfailureportal.com/api-manager/
- **🍎 Food-Base**: https://heartfailureportal.com/food-base/

## Troubleshooting

### Check Deployment Logs
```bash
ssh -i ./Food-Base/heart_portal_key root@129.212.181.161
tail -f /tmp/heart-portal-deploy.log
```

### Check Service Logs
```bash
# Main app logs
tail -f /tmp/main-app.log

# API Manager logs  
tail -f /tmp/api-manager.log

# Food-Base logs
tail -f /tmp/food-base.log
```

### Restart Individual Services
```bash
# Stop all services
pkill -f "python.*app.py"

# Start services manually
cd /opt/heart-portal/main-app && nohup ./venv/bin/python main_app.py > /tmp/main-app.log 2>&1 &
cd /opt/heart-portal/API-manager && nohup ./venv/bin/python app.py > /tmp/api-manager.log 2>&1 &
cd /opt/heart-portal/Food-Base && nohup ./venv/bin/python app.py > /tmp/food-base.log 2>&1 &
```

## Server Details

- **Server**: heartfailureportal.com (129.212.181.161)
- **Project Directory**: `/opt/heart-portal`
- **User**: `heartportal`
- **Services**: nginx (port 80), main-app (port 3000), API-manager (port 5000), Food-Base (port 5001)

## Environment Variables

The production server uses:
- **USDA_API_KEY**: Set in `/opt/heart-portal/API-manager/.env`
- All other environment variables are configured automatically

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