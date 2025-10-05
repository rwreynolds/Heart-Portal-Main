#!/bin/bash
# Start all Heart Portal applications using shared .env configuration

echo "🚀 Starting all Heart Portal applications using shared .env configuration..."

# Kill existing Python processes for our applications
echo "🧹 Cleaning up existing processes..."
pkill -f "main-app.*python" 2>/dev/null || true
pkill -f "Blog-Manager.*python" 2>/dev/null || true
pkill -f "Nutrition-Database.*python" 2>/dev/null || true
pkill -f "Food-Base.*python" 2>/dev/null || true
pkill -f "Sodium-Tracker.*python" 2>/dev/null || true
pkill -f "Fluid-Tracker.*python" 2>/dev/null || true
pkill -f "Weight-Tracker.*python" 2>/dev/null || true
pkill -f "BP-Monitor.*python" 2>/dev/null || true

# Wait for processes to terminate
sleep 2

echo "🌐 Starting applications (environment loaded from shared .env file)..."

# Change to project root directory
cd "$(dirname "$(dirname "$0")")"

# Main App (port 3000)
cd main-app && python3 main_app.py &
echo "✅ Main App started on port 3000"

# Blog Manager (port 5002)
cd ../Blog-Manager && python3 app.py &
echo "✅ Blog Manager started on port 5002"

# Nutrition Database (port 5000)
cd ../Nutrition-Database && python3 app.py &
echo "✅ Nutrition Database started on port 5000"

# Food Base (port 5001)
cd ../Food-Base && python3 app.py &
echo "✅ Food Base started on port 5001"

# Sodium Tracker (port 5003)
cd ../Sodium-Tracker && python3 app.py &
echo "✅ Sodium Tracker started on port 5003"

# Fluid Tracker (port 5004)
cd ../Fluid-Tracker && python3 app.py &
echo "✅ Fluid Tracker started on port 5004"

# Weight Tracker (port 5005)
cd ../Weight-Tracker && python3 app.py &
echo "✅ Weight Tracker started on port 5005"

# BP Monitor (port 5006)
cd ../BP-Monitor && python3 app.py &
echo "✅ BP Monitor started on port 5006"

echo ""
echo "🎉 All applications started using shared .env configuration!"
echo "📍 Access everything through: http://localhost:8080"
echo ""
echo "🛑 To stop all: pkill -f 'python.*app.py'"