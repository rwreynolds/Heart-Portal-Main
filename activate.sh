#!/bin/bash
# Heart Portal - Virtual Environment Activation Script
# Quick activation helper for development

echo "🍎 Activating Heart Portal Virtual Environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo ""
echo "📦 Python: $(python --version)"
echo "📍 Location: $(which python)"
echo ""
echo "Available commands:"
echo "  - deactivate          Exit virtual environment"
echo "  - pip list            Show installed packages"
echo "  - pip freeze          Export requirements"
echo ""
echo "🚀 Ready to develop!"
