"""
Main Flask Application for Heart Failure Portal
Serves landing page, blog, about pages
"""

from flask import Flask, render_template, request, jsonify, redirect, session, flash, url_for
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add shared directory to path for authentication module and URL helpers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from auth import init_auth_db, authenticate_user, create_user, get_current_user, login_required, create_session, invalidate_session, make_user_admin, get_all_users, deactivate_user, activate_user, remove_admin_privileges, delete_user
from url_helpers import (
    get_main_app_url, get_blog_url, get_nutrition_url, get_foodbase_url,
    get_sodium_url, get_fluid_url, get_weight_url, get_bp_url
)

# Import blog queries from local module (uses direct PostgreSQL connection to blog DB)
import blog_queries

app = Flask(__name__)
# Shared secret key for cross-application session compatibility
app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

# Configure session cookies for reverse proxy setup
# Production configuration for cross-app session sharing
app.config['SESSION_COOKIE_DOMAIN'] = '.heartfailureportal.com'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS required
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests

# Configure Jinja to look in multiple template directories
from jinja2 import FileSystemLoader, ChoiceLoader
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

# URL helpers are now imported from shared module

# Make URL functions and authentication context available in templates
app.jinja_env.globals.update(
    get_main_app_url=get_main_app_url,
    get_blog_url=get_blog_url,
    get_nutrition_url=get_nutrition_url,
    get_foodbase_url=get_foodbase_url,
    get_sodium_url=get_sodium_url,
    get_fluid_url=get_fluid_url,
    get_weight_url=get_weight_url,
    get_bp_url=get_bp_url,
    get_current_user=get_current_user
)


@app.route('/')
def landing_page():
    """Main landing page"""
    return render_template('landing.html')

@app.route('/blog')
def redirect_to_blog():
    """Redirect to Blog Manager - environment-aware"""
    return redirect(get_blog_url())

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
    return redirect(get_nutrition_url())

@app.route('/redirect/foodbase')
def redirect_to_foodbase():
    """Redirect to Food-Base - environment-aware"""
    return redirect(get_foodbase_url())

@app.route('/redirect/sodium')
def redirect_to_sodium():
    """Redirect to Sodium Tracker - environment-aware"""
    return redirect(get_sodium_url())

@app.route('/redirect/fluid')
def redirect_to_fluid():
    """Redirect to Fluid Tracker - environment-aware"""
    return redirect(get_fluid_url())

@app.route('/redirect/weight')
def redirect_to_weight():
    """Redirect to Weight Tracker - environment-aware"""
    return redirect(get_weight_url())

@app.route('/redirect/bp')
def redirect_to_bp():
    """Redirect to BP/HR Monitor - environment-aware"""
    return redirect(get_bp_url())

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error='Please enter both username and password')

        user = authenticate_user(username, password)
        if user:
            session_token = create_session(user.id)
            session['session_token'] = session_token
            session['user_id'] = user.id
            session['username'] = user.username

            # Redirect to requested page or landing page
            next_page = request.args.get('next', '/')
            return redirect(next_page)
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not all([username, email, password, confirm_password]):
            return render_template('register.html', error='All fields are required')

        if len(username) < 3 or len(username) > 20:
            return render_template('register.html', error='Username must be 3-20 characters long')

        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters long')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        # Create user
        result = create_user(username, email, password)

        if isinstance(result, dict) and 'error' in result:
            return render_template('register.html', error=result['error'])

        # Registration successful
        return render_template('register.html', success='Account created successfully! Please log in.')

    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    if 'session_token' in session:
        invalidate_session(session['session_token'])

    session.clear()
    return redirect(url_for('landing_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard (protected route)"""
    user = get_current_user()
    return render_template('dashboard.html', user=user)

# ADMIN ROUTES

@app.route('/admin')
@login_required
def admin_dashboard():
    """Main admin dashboard - requires admin privileges"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    # Get overview statistics
    all_users = get_all_users()
    pending_posts_count = blog_queries.get_pending_posts_count()

    stats = {
        'total_users': len(all_users),
        'admin_users': len([u for u in all_users if u['is_admin']]),
        'pending_posts': pending_posts_count,
        'active_users': len([u for u in all_users if u['is_active']])
    }

    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
def admin_users():
    """User management - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    users = get_all_users()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/promote/<int:user_id>', methods=['POST'])
@login_required
def admin_promote_user(user_id):
    """Promote user to admin"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    make_user_admin(user_id)
    flash('User promoted to admin successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/demote/<int:user_id>', methods=['POST'])
@login_required
def admin_demote_user(user_id):
    """Remove admin privileges from user"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    # Prevent self-demotion
    if current_user.id == user_id:
        flash('Cannot demote yourself!', 'error')
        return redirect(url_for('admin_users'))

    remove_admin_privileges(user_id)
    flash('Admin privileges removed successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/deactivate/<int:user_id>', methods=['POST'])
@login_required
def admin_deactivate_user(user_id):
    """Deactivate user account"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    # Prevent self-deactivation
    if current_user.id == user_id:
        flash('Cannot deactivate your own account!', 'error')
        return redirect(url_for('admin_users'))

    deactivate_user(user_id)
    flash('User account deactivated successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/activate/<int:user_id>', methods=['POST'])
@login_required
def admin_activate_user(user_id):
    """Activate user account"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    activate_user(user_id)
    flash('User account activated successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete user account (use with extreme caution)"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    # Prevent self-deletion
    if current_user.id == user_id:
        flash('Cannot delete your own account!', 'error')
        return redirect(url_for('admin_users'))

    delete_user(user_id)
    flash('User account deleted permanently!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/blog')
@login_required
def admin_blog():
    """Blog post moderation - redirect to Blog Manager admin"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    # Redirect to Blog Manager's admin interface
    return redirect(f"{get_blog_url()}admin")

@app.route('/admin/blog/approve/<int:post_id>', methods=['POST'])
@login_required
def admin_approve_post(post_id):
    """Approve pending post - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    review_notes = request.form.get('review_notes', '')
    success = approve_post(post_id, current_user.id, review_notes)

    if success:
        flash('Post approved and published!', 'success')
    else:
        flash('Failed to approve post.', 'error')

    return redirect(url_for('admin_blog'))

@app.route('/admin/blog/reject/<int:post_id>', methods=['POST'])
@login_required
def admin_reject_post(post_id):
    """Reject pending post - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    review_notes = request.form.get('review_notes', '')
    success = reject_post(post_id, current_user.id, review_notes)

    if success:
        flash('Post rejected.', 'success')
    else:
        flash('Failed to reject post.', 'error')

    return redirect(url_for('admin_blog'))

@app.route('/admin/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    """Delete any post - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('landing_page'))

    # Admin can delete any post (no author_id restriction)
    success = delete_post(post_id)

    if success:
        flash('Post deleted successfully!', 'success')
    else:
        flash('Failed to delete post.', 'error')

    return redirect(url_for('admin_blog'))

if __name__ == '__main__':
    # Initialize databases
    init_auth_db()
    init_blog_database()

    # Use debug=False in production, True for development
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'

    # Read port from environment variable (for staging) or use default
    port = int(os.getenv('PORT', 3000))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
