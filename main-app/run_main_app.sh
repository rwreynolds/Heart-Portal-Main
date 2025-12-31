#!/bin/bash
cd main-app
echo "Starting Heart Portal Main App with ClaudeExperiment features..."
echo ""
echo "New features enabled:"
echo "  ✅ Security Headers"
echo "  ✅ Centralized Logging"
echo "  ✅ Health Check Endpoint"
echo ""
echo "Visit in your browser:"
echo "  🌐 Main App: http://localhost:3000"
echo "  💚 Health Check: http://localhost:3000/health"
echo ""
echo "Press Ctrl+C to stop"
echo "======================================"
echo ""
python3 main_app.py
