"""
Main Flask Application for Heart Failure Portal
Serves landing page, blog, about pages
"""

from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import os

app = Flask(__name__)

# Configure Jinja to look in multiple template directories
from jinja2 import FileSystemLoader, ChoiceLoader
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

def get_main_app_url():
    """Get the main app URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com'
    return 'http://localhost:3000'

def get_blog_url():
    """Get the blog URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com/blog-manager/'
    return 'http://localhost:5002'

def get_nutrition_url():
    """Get the nutrition database URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com/nutrition-database/'
    return 'http://localhost:5000'

def get_foodbase_url():
    """Get the food base URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com/food-base/'
    return 'http://localhost:5001'

def get_sodium_url():
    """Get the sodium tracker URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com/sodium-tracker/'
    return 'http://localhost:5003'

def get_fluid_url():
    """Get the fluid tracker URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com/fluid-tracker/'
    return 'http://localhost:5004'

def get_weight_url():
    """Get the weight tracker URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com/weight-tracker/'
    return 'http://localhost:5005'

# Make URL functions available in templates
app.jinja_env.globals.update(
    get_main_app_url=get_main_app_url,
    get_blog_url=get_blog_url,
    get_nutrition_url=get_nutrition_url,
    get_foodbase_url=get_foodbase_url,
    get_sodium_url=get_sodium_url,
    get_fluid_url=get_fluid_url,
    get_weight_url=get_weight_url
)


@app.route('/')
def landing_page():
    """Main landing page"""
    return render_template('landing.html')

@app.route('/blog')
def redirect_to_blog():
    """Redirect to Blog Manager - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/blog-manager/')
    
    # Local development
    return redirect('http://localhost:5002')

@app.route('/about')
def about_portal():
    """About the portal page"""
    return render_template('about.html')

@app.route('/creator')
def about_creator():
    """About the creator page"""
    return render_template('creator.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form (optional)"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # You'd typically save this to a database or send an email
        # For now, just return a success response
        return jsonify({'success': True, 'message': 'Thank you for your message!'})
    
    return render_template('contact.html')

@app.route('/redirect/nutrition')
def redirect_to_nutrition():
    """Redirect to Nutrition Database - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/nutrition-database/')
    
    # Local development
    return redirect('http://localhost:5000')

@app.route('/redirect/foodbase')
def redirect_to_foodbase():
    """Redirect to Food-Base - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/food-base/')

    # Local development
    return redirect('http://localhost:5001')

@app.route('/redirect/sodium')
def redirect_to_sodium():
    """Redirect to Sodium Tracker - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/sodium-tracker/')

    # Local development
    return redirect('http://localhost:5003')

@app.route('/redirect/fluid')
def redirect_to_fluid():
    """Redirect to Fluid Tracker - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/fluid-tracker/')

    # Local development
    return redirect('http://localhost:5004')

@app.route('/redirect/weight')
def redirect_to_weight():
    """Redirect to Weight Tracker - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/weight-tracker/')

    # Local development
    return redirect('http://localhost:5005')

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Use debug=False in production, True for development
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, port=3000, host='0.0.0.0')
