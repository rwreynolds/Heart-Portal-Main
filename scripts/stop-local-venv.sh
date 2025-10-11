#!/bin/bash

# Stop all Heart Portal apps running locally

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "=========================================="
echo "🛑 Stop Heart Portal Apps (Local)"
echo "=========================================="
echo

log "Finding Flask processes on ports 3000, 5000-5005..."

# Get PIDs
PIDS=$(lsof -ti :3000,:5000,:5001,:5002,:5003,:5004,:5005 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    warning "No Flask apps running on these ports"
    exit 0
fi

echo "Found processes:"
for pid in $PIDS; do
    echo "  PID $pid: $(ps -p $pid -o command= | head -c 80)"
done
echo

read -p "Kill these processes? (y/n): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    for pid in $PIDS; do
        log "Killing process $pid..."
        kill -9 $pid 2>/dev/null || true
    done

    sleep 1

    # Verify they're stopped
    REMAINING=$(lsof -ti :3000,:5000,:5001,:5002,:5003,:5004,:5005 2>/dev/null || true)
    if [ -z "$REMAINING" ]; then
        success "All Flask apps stopped"
    else
        warning "Some processes still running: $REMAINING"
        echo "Try: kill -9 $REMAINING"
    fi
else
    echo "Cancelled"
fi

echo
