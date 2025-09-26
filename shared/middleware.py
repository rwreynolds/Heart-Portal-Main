"""
Authentication middleware for private applications
Handles login redirection for apps that require authentication
"""

from flask import request, redirect, session
import requests


def require_login_middleware(app):
    """
    Middleware to redirect users to login if they're not authenticated
    Only applies to private apps (nutrition, trackers, food storage)
    """

    @app.before_request
    def check_authentication():
        # Skip authentication check for certain paths
        exempt_paths = [
            '/login', '/register', '/logout',
            '/static/', '/favicon.ico'
        ]

        # Skip if this is an exempt path
        if any(request.path.startswith(path) for path in exempt_paths):
            return None

        # Check if user has a session token
        session_token = session.get('session_token')

        if not session_token:
            # Not logged in - redirect to main app login with return URL
            main_app_url = get_main_app_url()
            return_url = request.url
            return redirect(f"{main_app_url}/login?next={return_url}")

        # Validate session token with main app
        try:
            # Try to validate the session by making a request to the main app
            response = requests.get(f"{get_main_app_url()}/dashboard",
                                  cookies={'session': session_token},
                                  timeout=5)

            if response.status_code == 302:  # Redirect means not authenticated
                # Clear invalid session and redirect to login
                session.clear()
                main_app_url = get_main_app_url()
                return_url = request.url
                return redirect(f"{main_app_url}/login?next={return_url}")

        except requests.RequestException:
            # If we can't reach the main app, allow access but log the issue
            pass

        return None


def get_main_app_url():
    """Get the main app URL based on environment"""
    import os
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com'
    return 'http://localhost:3000'