"""
Quick test script to verify health check endpoint works
"""
import sys
sys.path.insert(0, '.')

from flask import Flask
from shared.health_check import create_health_check_endpoint
from shared.security_headers import init_security_headers
from shared.logger import setup_logger

# Create Flask app
app = Flask(__name__)
logger = setup_logger('test-app')

# Add security headers
init_security_headers(app)

# Add health check endpoint (no database for this test)
create_health_check_endpoint(app, 'test-app')

@app.route('/')
def home():
    logger.info("Home page accessed")
    return "Test App - ClaudeExperiment Branch<br><a href='/health'>Check Health Endpoint</a>"

if __name__ == '__main__':
    logger.info("Starting test application")
    app.run(debug=True, port=8888)
