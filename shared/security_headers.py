"""
Security headers middleware for Flask applications
Implements security best practices to protect against common vulnerabilities
"""

from flask import Flask, Response
from typing import Callable


def add_security_headers(response: Response) -> Response:
    """
    Add security headers to all responses

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Strict-Transport-Security: Force HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features

    Args:
        response: Flask response object

    Returns:
        Response with added security headers
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # Enable XSS protection in older browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Force HTTPS in production (31536000 seconds = 1 year)
    # Only add if the request was made over HTTPS
    if response.headers.get('X-Forwarded-Proto') == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy - restrict resource loading
    # Allows self, inline scripts/styles (needed for current templates), and CDNs
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy

    # Control referrer information leakage
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Restrict browser features
    response.headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=(), '
        'payment=(), '
        'usb=()'
    )

    return response


def init_security_headers(app: Flask) -> None:
    """
    Initialize security headers for a Flask application

    Usage:
        from shared.security_headers import init_security_headers

        app = Flask(__name__)
        init_security_headers(app)

    Args:
        app: Flask application instance
    """
    @app.after_request
    def set_security_headers(response: Response) -> Response:
        return add_security_headers(response)
