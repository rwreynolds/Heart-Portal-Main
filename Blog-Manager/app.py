"""
Blog Manager Flask Application for Heart Failure Portal
Serves blog posts and handles blog-related functionality
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
import os
import sys
from jinja2 import ChoiceLoader, FileSystemLoader
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add shared directory to path for authentication module and URL helpers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from auth import get_current_user
from url_helpers import (
    get_main_app_url, get_blog_url, get_nutrition_url, get_foodbase_url,
    get_sodium_url, get_fluid_url, get_weight_url
)

# Import database functions
from database import (
    init_blog_database, get_published_posts, get_post_by_slug,
    get_user_posts, get_pending_posts, create_post, update_post,
    approve_post, reject_post, delete_post, migrate_sample_posts
)

app = Flask(__name__)
# Shared secret key for cross-application session compatibility
app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

# Configure session cookies for reverse proxy setup
app.config['SESSION_COOKIE_DOMAIN'] = '.heartfailureportal.com'  # Share cookies across all subdomains
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests

# Configure Jinja2 to use shared templates
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

# URL helpers are now imported from shared module

# Make functions available in templates
@app.context_processor
def utility_processor():
    return dict(
        get_main_app_url=get_main_app_url,
        get_blog_url=get_blog_url,
        get_nutrition_url=get_nutrition_url,
        get_foodbase_url=get_foodbase_url,
        get_sodium_url=get_sodium_url,
        get_fluid_url=get_fluid_url,
        get_weight_url=get_weight_url
    )

# Register template global functions
app.jinja_env.globals.update(
    get_main_app_url=get_main_app_url,
    get_blog_url=get_blog_url,
    get_nutrition_url=get_nutrition_url,
    get_foodbase_url=get_foodbase_url,
    get_sodium_url=get_sodium_url,
    get_fluid_url=get_fluid_url,
    get_weight_url=get_weight_url,
    get_current_user=get_current_user
)

# PUBLIC BLOG ROUTES (No authentication required)

@app.route('/')
def blog_list():
    """Public blog post listing page"""
    posts = get_published_posts()
    current_user = get_current_user()
    return render_template('blog.html', posts=posts, current_user=current_user)

@app.route('/post/<slug>')
def blog_post(slug):
    """Individual blog post page by slug"""
    post = get_post_by_slug(slug)
    if not post:
        return render_template('404.html'), 404
    return render_template('blog_post.html', post=post)

# PRIVATE BLOG ROUTES (Authentication required)

@app.route('/dashboard')
def user_dashboard():
    """User blog dashboard - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    # Get user's posts
    user_posts = get_user_posts(current_user['id'])

    return render_template('user_dashboard.html', posts=user_posts)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    """Create new blog post - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt', '')
        visibility = request.form.get('visibility', 'private')
        tags = request.form.get('tags', '')

        if title and content:
            post_id = create_post(
                title=title,
                content=content,
                author_id=current_user['id'],
                author_name=current_user['username'],
                excerpt=excerpt,
                visibility=visibility,
                tags=tags
            )

            flash('Post created successfully!', 'success')
            if visibility == 'public':
                flash('Your public post has been submitted for review.', 'info')

            return redirect(url_for('user_dashboard'))
        else:
            flash('Title and content are required.', 'error')

    return render_template('create_post.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    """Edit existing post - requires login and ownership"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    # Get user's posts to verify ownership
    user_posts = get_user_posts(current_user['id'])
    post = next((p for p in user_posts if p['id'] == post_id), None)

    if not post:
        flash('Post not found or access denied.', 'error')
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        visibility = request.form.get('visibility')
        tags = request.form.get('tags')

        success = update_post(
            post_id=post_id,
            title=title,
            content=content,
            excerpt=excerpt,
            visibility=visibility,
            tags=tags
        )

        if success:
            flash('Post updated successfully!', 'success')
            if visibility == 'public' and post['status'] != 'published':
                flash('Your public post has been submitted for review.', 'info')
        else:
            flash('Failed to update post.', 'error')

        return redirect(url_for('user_dashboard'))

    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_user_post(post_id):
    """Delete post - requires login and ownership"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    success = delete_post(post_id, author_id=current_user['id'])

    if success:
        flash('Post deleted successfully!', 'success')
    else:
        flash('Failed to delete post or access denied.', 'error')

    return redirect(url_for('user_dashboard'))

# ADMIN ROUTES (Site owner only)

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for post review - requires admin privileges"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login")

    pending_posts = get_pending_posts()

    return render_template('admin_dashboard.html', posts=pending_posts)

@app.route('/admin/approve/<int:post_id>', methods=['POST'])
def approve_user_post(post_id):
    """Approve pending post - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('blog_list'))

    review_notes = request.form.get('review_notes', '')
    success = approve_post(post_id, current_user['id'], review_notes)

    if success:
        flash('Post approved and published!', 'success')
    else:
        flash('Failed to approve post.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:post_id>', methods=['POST'])
def reject_user_post(post_id):
    """Reject pending post - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('blog_list'))

    review_notes = request.form.get('review_notes', '')
    success = reject_post(post_id, current_user['id'], review_notes)

    if success:
        flash('Post rejected.', 'success')
    else:
        flash('Failed to reject post.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:post_id>', methods=['POST'])
def delete_admin_post(post_id):
    """Delete any post - admin only"""
    current_user = get_current_user()
    if not current_user or not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('blog_list'))

    # Admin can delete any post (no author_id restriction)
    success = delete_post(post_id)

    if success:
        flash('Post deleted successfully!', 'success')
    else:
        flash('Failed to delete post.', 'error')

    return redirect(url_for('admin_dashboard'))

# Environment-aware redirect functions for Tools menu
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
    # Initialize database and migrate sample posts
    init_blog_database()
    migrate_sample_posts()

    # Read port from environment variable (for staging) or use default
    port = int(os.getenv('PORT', 5002))
    app.run(debug=True, port=port, host='0.0.0.0')