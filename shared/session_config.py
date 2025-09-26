"""
Shared session configuration for all Heart Portal Flask applications
Ensures consistent session cookie settings across all apps in reverse proxy mode
"""
import os

def configure_session(app):
    """Configure Flask app with shared session settings"""
    # Shared secret key for cross-application session compatibility
    app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

    # Configure session cookies for localhost development
    app.config['SESSION_COOKIE_DOMAIN'] = None  # Works for localhost
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_SECURE'] = False  # HTTP for local dev
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests