"""
Main Flask Application for Heart Failure Portal
Serves landing page, blog, about pages
"""

from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import os

app = Flask(__name__)


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

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000, host='0.0.0.0')
