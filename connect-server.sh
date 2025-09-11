#!/bin/bash

# Heart Portal Server Connection Helper
# Quick SSH connection to production server

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

# Server configuration
SERVER_HOST="129.212.181.161"
SERVER_USER="heartportal"
SSH_KEY="./Food-Base/heart_portal_key"
PROJECT_DIR="/opt/heart-portal"

echo -e "${BLUE}🔗 Connecting to Heart Portal server...${NC}"
echo "Host: $SERVER_HOST"
echo "User: $SERVER_USER"
echo "Key: $SSH_KEY"
echo

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ SSH key not found: $SSH_KEY${NC}"
    exit 1
fi

# Connect to server
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" -t "cd $PROJECT_DIR && exec \$SHELL"