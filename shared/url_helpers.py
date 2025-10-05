"""
Shared URL helpers for reverse proxy setup
Provides consistent URL generation across all Flask applications
"""

import os

def is_production_mode():
    """Check if running in production environment"""
    return os.environ.get('PRODUCTION_MODE', '').lower() == 'true' or \
           (os.path.exists('/etc/hostname') and 'heartfailure' in open('/etc/hostname').read())

def is_staging_mode():
    """Check if running in staging environment"""
    return os.environ.get('STAGING_MODE', '').lower() == 'true'

def is_reverse_proxy_mode():
    """Check if running behind reverse proxy (nginx on port 8080)"""
    return os.environ.get('REVERSE_PROXY_MODE', '').lower() == 'true'

def get_base_url():
    """Get the base URL for the current environment"""
    if is_production_mode():
        return 'https://heartfailureportal.com'
    elif is_staging_mode():
        return os.environ.get('STAGING_BASE_URL', 'http://heartfailureportal.com:8081')
    elif is_reverse_proxy_mode():
        return 'http://localhost:8080'
    else:
        # Fallback to direct port access for development
        return 'http://localhost:3000'

def get_main_app_url():
    """Get the main app URL"""
    if is_production_mode() or is_staging_mode() or is_reverse_proxy_mode():
        return get_base_url()
    else:
        return 'http://localhost:3000'

def get_blog_url():
    """Get the blog URL"""
    if is_production_mode():
        return f"{get_base_url()}/blog-manager/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/blog/"
    else:
        return 'http://localhost:5002'

def get_nutrition_url():
    """Get the nutrition database URL"""
    if is_production_mode():
        return f"{get_base_url()}/nutrition-database/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/nutrition/"
    else:
        return 'http://localhost:5000'

def get_foodbase_url():
    """Get the food-base URL"""
    if is_production_mode():
        return f"{get_base_url()}/food-base/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/food/"
    else:
        return 'http://localhost:5001'

def get_sodium_url():
    """Get the sodium tracker URL"""
    if is_production_mode():
        return f"{get_base_url()}/sodium-tracker/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/sodium/"
    else:
        return 'http://localhost:5003'

def get_fluid_url():
    """Get the fluid tracker URL"""
    if is_production_mode():
        return f"{get_base_url()}/fluid-tracker/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/fluid/"
    else:
        return 'http://localhost:5004'

def get_weight_url():
    """Get the weight tracker URL"""
    if is_production_mode():
        return f"{get_base_url()}/weight-tracker/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/weight/"
    else:
        return 'http://localhost:5005'

def get_bp_url():
    """Get the blood pressure monitor URL"""
    if is_production_mode():
        return f"{get_base_url()}/bp-monitor/"
    elif is_staging_mode() or is_reverse_proxy_mode():
        return f"{get_base_url()}/bp-monitor/"
    else:
        return 'http://localhost:5006'