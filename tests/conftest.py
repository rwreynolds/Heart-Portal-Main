"""
Pytest configuration and shared fixtures for Heart Portal tests
"""

import pytest
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePassword123!'
    }


@pytest.fixture
def test_blog_post_data():
    """Sample blog post data for testing"""
    return {
        'title': 'Test Blog Post',
        'content': 'This is test content for the blog post.',
        'excerpt': 'This is a test excerpt.',
        'author_id': 1,
        'author_name': 'testuser',
        'tags': 'test,nutrition,heart-health'
    }


@pytest.fixture
def test_sodium_entry_data():
    """Sample sodium tracker entry for testing"""
    return {
        'user_id': 1,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'food_item': 'Test Food',
        'sodium_mg': 500,
        'serving_size': '1 cup',
        'meal_type': 'lunch',
        'notes': 'Test entry'
    }


@pytest.fixture
def test_fluid_entry_data():
    """Sample fluid tracker entry for testing"""
    return {
        'user_id': 1,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'beverage_name': 'Water',
        'beverage_type': 'water',
        'volume_ml': 250,
        'time_of_day': '10:00',
        'notes': 'Test entry'
    }


@pytest.fixture
def test_weight_entry_data():
    """Sample weight tracker entry for testing"""
    return {
        'user_id': 1,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'weight_lbs': 180.5,
        'notes': 'Morning weight'
    }


@pytest.fixture
def test_bp_entry_data():
    """Sample BP monitor entry for testing"""
    return {
        'user_id': 1,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'systolic': 120,
        'diastolic': 80,
        'heart_rate': 72,
        'notes': 'Resting BP'
    }


@pytest.fixture
def mock_database_url():
    """Mock database URL for testing (use SQLite in-memory)"""
    return 'sqlite:///:memory:'


@pytest.fixture
def date_range():
    """Date range for testing (last 7 days)"""
    today = datetime.now()
    return [
        (today - timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(7)
    ]
