"""
Unit tests for shared/security_headers.py
Tests security header middleware
"""

import pytest
from flask import Flask
from shared.security_headers import add_security_headers, init_security_headers


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    init_security_headers(app)

    @app.route('/test')
    def test_route():
        return 'OK'

    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_security_headers_present(client):
    """Test that all security headers are added to responses"""
    response = client.get('/test')

    # Check all expected headers are present
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert 'X-XSS-Protection' in response.headers
    assert 'Content-Security-Policy' in response.headers
    assert 'Referrer-Policy' in response.headers
    assert 'Permissions-Policy' in response.headers


def test_x_content_type_options(client):
    """Test X-Content-Type-Options header value"""
    response = client.get('/test')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_x_frame_options(client):
    """Test X-Frame-Options header value"""
    response = client.get('/test')
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'


def test_x_xss_protection(client):
    """Test X-XSS-Protection header value"""
    response = client.get('/test')
    assert response.headers['X-XSS-Protection'] == '1; mode=block'


def test_csp_header_present(client):
    """Test that CSP header is present and configured"""
    response = client.get('/test')
    csp = response.headers['Content-Security-Policy']

    assert "default-src 'self'" in csp
    assert "script-src" in csp
    assert "style-src" in csp


def test_referrer_policy(client):
    """Test Referrer-Policy header value"""
    response = client.get('/test')
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'


def test_permissions_policy(client):
    """Test Permissions-Policy header restricts dangerous features"""
    response = client.get('/test')
    permissions = response.headers['Permissions-Policy']

    assert 'geolocation=()' in permissions
    assert 'microphone=()' in permissions
    assert 'camera=()' in permissions
