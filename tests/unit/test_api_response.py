"""
Unit tests for shared/api_response.py
Tests standardized API response formatting
"""

import pytest
from flask import Flask
from shared.api_response import (
    success_response,
    error_response,
    validation_error_response,
    not_found_response,
    unauthorized_response,
    forbidden_response,
    server_error_response
)


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    return app


def test_success_response_with_data(app):
    """Test success response with data"""
    with app.app_context():
        response, status_code = success_response(
            data={'user_id': 1, 'username': 'testuser'},
            message="User created successfully",
            status_code=201
        )

        assert status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['message'] == 'User created successfully'
        assert data['data']['user_id'] == 1
        assert data['data']['username'] == 'testuser'


def test_success_response_without_data(app):
    """Test success response without data"""
    with app.app_context():
        response, status_code = success_response()

        assert status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['message'] == 'Success'
        assert 'data' not in data


def test_error_response_basic(app):
    """Test basic error response"""
    with app.app_context():
        response, status_code = error_response(
            message="Invalid input",
            status_code=400
        )

        assert status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert data['message'] == 'Invalid input'


def test_error_response_with_errors(app):
    """Test error response with error details"""
    with app.app_context():
        errors = {
            'email': ['Email is required'],
            'password': ['Password too short']
        }
        response, status_code = error_response(
            message="Validation failed",
            status_code=400,
            errors=errors
        )

        assert status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert data['errors'] == errors


def test_validation_error_response(app):
    """Test validation error response (422)"""
    with app.app_context():
        errors = {'field': ['Error message']}
        response, status_code = validation_error_response(errors)

        assert status_code == 422
        data = response.get_json()
        assert data['status'] == 'error'
        assert data['message'] == 'Validation failed'


def test_not_found_response(app):
    """Test 404 not found response"""
    with app.app_context():
        response, status_code = not_found_response('Blog post', 123)

        assert status_code == 404
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Blog post not found' in data['message']
        assert '123' in data['message']


def test_unauthorized_response(app):
    """Test 401 unauthorized response"""
    with app.app_context():
        response, status_code = unauthorized_response()

        assert status_code == 401
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Authentication required' in data['message']


def test_forbidden_response(app):
    """Test 403 forbidden response"""
    with app.app_context():
        response, status_code = forbidden_response()

        assert status_code == 403
        data = response.get_json()
        assert data['status'] == 'error'


def test_server_error_response(app):
    """Test 500 server error response"""
    with app.app_context():
        response, status_code = server_error_response(error_id='ERR123')

        assert status_code == 500
        data = response.get_json()
        assert data['status'] == 'error'
        assert data['errors']['error_id'] == 'ERR123'
