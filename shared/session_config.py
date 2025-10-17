"""
Shared session configuration for all Heart Portal Flask applications
Ensures consistent session cookie settings across all apps in reverse proxy mode
"""
import os

def configure_session(app):
    """Configure Flask app with shared session settings"""
    # Shared secret key for cross-application session compatibility
    app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

    # Check if running in staging or production mode
    is_staging = os.environ.get('STAGING_MODE', '').lower() == 'true'
    is_production = os.environ.get('PRODUCTION_MODE', '').lower() == 'true' or \
                    (os.path.exists('/etc/hostname') and 'heartfailure' in open('/etc/hostname').read())

    if is_staging or is_production:
        # Configure session cookies for production/staging with reverse proxy
        app.config['SESSION_COOKIE_DOMAIN'] = '.heartfailureportal.com'  # Share cookies across all subdomains
        app.config['SESSION_COOKIE_PATH'] = '/'
        app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
        app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests
    else:
        # Configure session cookies for localhost development
        app.config['SESSION_COOKIE_DOMAIN'] = None  # Works for localhost
        app.config['SESSION_COOKIE_PATH'] = '/'
        app.config['SESSION_COOKIE_SECURE'] = False  # HTTP for local dev
        app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests