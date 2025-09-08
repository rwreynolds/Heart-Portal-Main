# Local Development Guide

This guide ensures you always work in your local project and never accidentally make changes on the server.

## 🔍 Quick Environment Check

**Before starting any work, always run:**

```bash
./dev-check.sh
```

This verifies:
- ✅ You're in the correct local directory
- ✅ You're not accidentally SSH'd into the server
- ✅ All project files are present
- ✅ Git is set up correctly

## 🏠 Local Development Rules

### ✅ DO (Local Development)
- **Always work in:** `/Users/mrrobot/VSCodeProjects/Heart-Portal-Main/`
- **Edit files in:** VSCode on your local machine
- **Test with:** Local development servers
- **Commit changes:** From your local project
- **Deploy with:** `./deploy.sh` from local project

### ❌ DON'T (Server Changes)
- **Never SSH into server** to edit code files
- **Never edit files** directly on heartfailureportal.com
- **Never make changes** in `/opt/heart-portal/` on server
- **Never commit** from the server

## 🖥️ Local Development Servers

Start your local development environment:

```bash
# Terminal 1: Main App
cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main/main-app
python main_app.py
# Runs on: http://localhost:3000

# Terminal 2: API Manager
cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main/API-manager  
python app.py
# Runs on: http://localhost:5000

# Terminal 3: Food-Base
cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main/Food-Base
python app.py  
# Runs on: http://localhost:5001
```

## 🔄 Proper Development Workflow

### 1. **Start Development Session**
```bash
cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main
./dev-check.sh  # Verify environment
```

### 2. **Make Changes**
- Open VSCode in the local project directory
- Edit files locally
- Test with local development servers

### 3. **Test Changes**
- Visit http://localhost:3000, :5000, :5001
- Verify your changes work correctly
- Add/remove test data in local database

### 4. **Commit Changes**
```bash
git add .
git commit -m "Description of your changes"
```

### 5. **Deploy to Production**
```bash
./deploy.sh  # Deploys code only, preserves production database
```

## 📁 Directory Structure Guide

**Your Local Project:**
```
/Users/mrrobot/VSCodeProjects/Heart-Portal-Main/
├── 📁 API-manager/           # Edit these files locally
├── 📁 Food-Base/            
├── 📁 main-app/             
├── 🚀 deploy.sh             # Deploy to production
├── 📥 download-database.sh   # Get production data
├── 🔍 dev-check.sh          # Verify environment
└── 📚 *.md                  # Documentation
```

**Production Server (DON'T EDIT):**
```
/opt/heart-portal/           # Server files - hands off!
```

## 🛡️ Safety Checks

### Before Making Any Changes:
1. Run `./dev-check.sh` 
2. Confirm you see: `✅ You're on your local machine (not the server)`
3. Confirm directory: `/Users/mrrobot/VSCodeProjects/Heart-Portal-Main`

### If You Accidentally SSH to Server:
```bash
exit  # Leave the server immediately
cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main  # Go to local project
./dev-check.sh  # Verify you're local
```

## 🗄️ Database Management

### Local Database (for testing):
- **Location:** `./Food-Base/database/food_base.db`
- **Purpose:** Testing with real data
- **Changes:** Stay local, never deployed

### Production Database (read-only for you):
- **Location:** Server only
- **Access:** Download with `./download-database.sh`
- **Protection:** Automatically preserved during deployments

### Sync Production Data:
```bash
./download-database.sh  # Downloads production database to local
```

## 🚨 Common Mistakes to Avoid

### ❌ Wrong: Editing on Server
```bash
ssh root@129.212.181.161
cd /opt/heart-portal
nano API-manager/app.py  # DON'T DO THIS!
```

### ✅ Right: Editing Locally  
```bash
cd /Users/mrrobot/VSCodeProjects/Heart-Portal-Main
code API-manager/app.py  # Edit in VSCode locally
```

### ❌ Wrong: Server Git Commands
```bash
# On server - DON'T DO THIS!
git add . && git commit -m "changes"  
```

### ✅ Right: Local Git Commands
```bash
# In local project - CORRECT!
git add . && git commit -m "changes"
./deploy.sh  # Deploy from local
```

## 🎯 Quick Reference

| Task | Command | Where |
|------|---------|-------|
| Check environment | `./dev-check.sh` | Local |
| Start development | `python app.py` | Local |
| Make changes | Use VSCode | Local |
| Test changes | http://localhost:* | Local |
| Commit changes | `git commit` | Local |
| Deploy changes | `./deploy.sh` | Local |
| Get production data | `./download-database.sh` | Local |

## 🆘 Need Help?

If you're unsure whether you're working locally:

1. **Run:** `./dev-check.sh`
2. **Look for:** `✅ You're on your local machine`  
3. **Verify path:** `/Users/mrrobot/VSCodeProjects/Heart-Portal-Main`

**Remember:** When in doubt, always work locally and deploy with `./deploy.sh`!