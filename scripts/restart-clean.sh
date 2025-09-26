#!/bin/bash

echo "🧹 Stopping all Flask applications..."

# Kill all Python processes that might be running Flask apps
pkill -f "python3.*app.py" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Wait for cleanup
sleep 3

echo "🚀 Starting all applications using shared .env configuration..."

# Change to project root directory
cd "$(dirname "$(dirname "$0")")"

# Start all services (environment loaded from shared .env file)
echo "▶️ Starting Main App (port 3000)..."
cd main-app && python3 main_app.py &
MAIN_PID=$!

echo "▶️ Starting Nutrition Database (port 5000)..."
cd ../Nutrition-Database && python3 app.py &
NUTRITION_PID=$!

echo "▶️ Starting Food Base (port 5001)..."
cd ../Food-Base && python3 app.py &
FOOD_PID=$!

echo "▶️ Starting Blog Manager (port 5002)..."
cd ../Blog-Manager && python3 app.py &
BLOG_PID=$!

echo "▶️ Starting Sodium Tracker (port 5003)..."
cd ../Sodium-Tracker && python3 app.py &
SODIUM_PID=$!

echo "▶️ Starting Fluid Tracker (port 5004)..."
cd ../Fluid-Tracker && python3 app.py &
FLUID_PID=$!

echo "▶️ Starting Weight Tracker (port 5005)..."
cd ../Weight-Tracker && python3 app.py &
WEIGHT_PID=$!

# Wait a moment for startup
sleep 2

echo ""
echo "✅ All applications started with PIDs:"
echo "   Main App: $MAIN_PID"
echo "   Nutrition: $NUTRITION_PID"
echo "   Food Base: $FOOD_PID"
echo "   Blog: $BLOG_PID"
echo "   Sodium: $SODIUM_PID"
echo "   Fluid: $FLUID_PID"
echo "   Weight: $WEIGHT_PID"
echo ""
echo "🌐 Access through: http://localhost:8080"
echo "📊 Navigation should now use reverse proxy paths:"
echo "   • Blog: http://localhost:8080/blog/"
echo "   • Nutrition: http://localhost:8080/nutrition/"
echo "   • Food Storage: http://localhost:8080/food/"
echo "   • Sodium Tracker: http://localhost:8080/sodium/"
echo "   • Fluid Tracker: http://localhost:8080/fluid/"
echo "   • Weight Tracker: http://localhost:8080/weight/"
echo ""
echo "🛑 To stop: pkill -f 'python.*app.py'"