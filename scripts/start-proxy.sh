#!/bin/bash
# Start nginx reverse proxy for Heart Portal development

echo "🚀 Starting Heart Portal with Reverse Proxy..."

# Check if nginx is available
if ! command -v nginx &> /dev/null; then
    echo "❌ nginx not found. Please install nginx first:"
    echo "   brew install nginx"
    exit 1
fi

# Kill any existing nginx processes
echo "🧹 Cleaning up existing nginx processes..."
pkill nginx 2>/dev/null || true

# Start nginx with our configuration
echo "🌐 Starting nginx reverse proxy on http://localhost:8080..."
nginx -c "$(pwd)/nginx-dev.conf" -p "$(pwd)"

echo "✅ Reverse proxy started!"
echo ""
echo "📍 Access your applications at:"
echo "   🏠 Main App:         http://localhost:8080/"
echo "   📝 Blog:            http://localhost:8080/blog/"
echo "   🔍 Nutrition:       http://localhost:8080/nutrition/"
echo "   🍎 Food Storage:    http://localhost:8080/food/"
echo "   🧂 Sodium Tracker:  http://localhost:8080/sodium/"
echo "   💧 Fluid Tracker:   http://localhost:8080/fluid/"
echo "   ⚖️ Weight Tracker:  http://localhost:8080/weight/"
echo ""
echo "🛑 To stop: pkill nginx"