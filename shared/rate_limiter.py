"""
Rate limiting configuration for Heart Portal
Protects against brute force attacks and API abuse
"""

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os


def get_identifier():
    """
    Get unique identifier for rate limiting
    Uses X-Forwarded-For if behind reverse proxy, otherwise remote address
    """
    # Check if behind reverse proxy (Nginx)
    if request.headers.get('X-Forwarded-For'):
        # Get the first IP in the chain (actual client)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return get_remote_address()


# Initialize limiter with memory storage (use Redis in production for distributed rate limiting)
# Storage can be configured via environment variable
storage_uri = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')

limiter = Limiter(
    key_func=get_identifier,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=storage_uri,
    strategy="fixed-window",  # or "moving-window" for more accuracy
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


def init_rate_limiter(app: Flask) -> Limiter:
    """
    Initialize rate limiter for a Flask application

    Usage:
        from shared.rate_limiter import init_rate_limiter

        app = Flask(__name__)
        limiter = init_rate_limiter(app)

        # In routes:
        @app.route('/login', methods=['POST'])
        @limiter.limit("5 per minute")
        def login():
            ...

    Args:
        app: Flask application instance

    Returns:
        Configured Limiter instance
    """
    limiter.init_app(app)
    return limiter


# Common rate limit decorators
def auth_rate_limit():
    """Rate limit for authentication endpoints: 5 attempts per minute"""
    return limiter.limit("5 per minute")


def api_rate_limit():
    """Rate limit for API endpoints: 100 requests per hour"""
    return limiter.limit("100 per hour")


def strict_rate_limit():
    """Strict rate limit for sensitive operations: 10 per hour"""
    return limiter.limit("10 per hour")


def generous_rate_limit():
    """Generous rate limit for read-only endpoints: 1000 per hour"""
    return limiter.limit("1000 per hour")
