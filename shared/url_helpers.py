"""
Shared URL helpers for reverse proxy setup
Provides consistent URL generation across all Flask applications
"""

import os

def is_reverse_proxy_mode():
    """Check if running behind reverse proxy (nginx on port 8080)"""
    return os.environ.get('REVERSE_PROXY_MODE', '').lower() == 'true'

def get_base_url():
    """Get the base URL for the reverse proxy setup"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080'
    else:
        # Fallback to direct port access for development
        return 'http://localhost:3000'

def get_main_app_url():
    """Get the main app URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080'
    else:
        return 'http://localhost:3000'

def get_blog_url():
    """Get the blog URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080/blog/'
    else:
        return 'http://localhost:5002'

def get_nutrition_url():
    """Get the nutrition database URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080/nutrition'
    else:
        return 'http://localhost:5000'

def get_foodbase_url():
    """Get the food-base URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080/food'
    else:
        return 'http://localhost:5001'

def get_sodium_url():
    """Get the sodium tracker URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080/sodium'
    else:
        return 'http://localhost:5003'

def get_fluid_url():
    """Get the fluid tracker URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080/fluid'
    else:
        return 'http://localhost:5004'

def get_weight_url():
    """Get the weight tracker URL"""
    if is_reverse_proxy_mode():
        return 'http://localhost:8080/weight'
    else:
        return 'http://localhost:5005'