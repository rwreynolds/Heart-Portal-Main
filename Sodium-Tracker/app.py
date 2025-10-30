"""
Sodium-Tracker Component - Flask Application
Tracks daily sodium intake for heart failure patients
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import os
import sys
from datetime import datetime, date
import json
from dotenv import load_dotenv
from urllib.parse import quote
from zoneinfo import ZoneInfo

# Load environment variables from both shared .env and app-specific .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # Shared .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # App-specific .env (overrides shared)

# Add shared directory to path for authentication module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from auth import get_current_user

# Import shared URL helpers
from url_helpers import (
    get_main_app_url, get_blog_url, get_nutrition_url, get_foodbase_url,
    get_sodium_url, get_fluid_url, get_weight_url, get_bp_url, is_reverse_proxy_mode
)

# Import database functions
import database as db

app = Flask(__name__)
# Shared secret key for cross-application session compatibility
app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

# Configure session cookies for reverse proxy setup
app.config['SESSION_COOKIE_DOMAIN'] = '.heartfailureportal.com'  # Share cookies across all subdomains
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests

# Configure Jinja to look in multiple template directories
from jinja2 import FileSystemLoader, ChoiceLoader
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

# Timezone configuration
TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')  # Default to Eastern Time

def get_current_date():
    """Get current date in configured timezone"""
    return datetime.now(ZoneInfo(TIMEZONE)).date()

# URL helpers are now imported from shared module

# Make URL functions available in templates
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

def init_database():
    """Initialize the database and set default settings"""
    db.init_sodium_database()

    # Insert default settings if they don't exist
    settings = db.get_all_settings()
    if 'default_daily_goal' not in settings:
        db.update_setting('default_daily_goal', '2300')
    if 'alert_threshold' not in settings:
        db.update_setting('alert_threshold', '80')

def get_daily_intake(target_date=None):
    """Get total sodium intake for a specific date"""
    if target_date is None:
        target_date = get_current_date().isoformat()
    return db.get_daily_total(target_date)

def get_daily_goal(target_date=None):
    """Get daily sodium goal for a specific date"""
    if target_date is None:
        target_date = get_current_date().isoformat()

    # Try to get specific goal for the date
    goal = db.get_daily_goal(target_date)
    if goal:
        return int(goal)

    # Fall back to default goal
    default_goal = db.get_default_daily_goal()
    return int(default_goal)

@app.route('/')
def index():
    """Main sodium tracker dashboard - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    today = get_current_date()
    today_str = today.isoformat()

    # Get today's intake
    daily_intake = get_daily_intake(today_str)
    daily_goal = get_daily_goal(today_str)

    # Calculate percentage
    percentage = (daily_intake / daily_goal * 100) if daily_goal > 0 else 0

    # Get recent entries
    entries = db.get_entries(date=today_str, limit=10)

    return render_template('index.html',
                         daily_intake=daily_intake,
                         daily_goal=daily_goal,
                         percentage=round(percentage, 1),
                         entries=entries,
                         today=today_str,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url())

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    """Add a new sodium entry - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    if request.method == 'POST':
        data = request.form
        entry_date = data.get('date', get_current_date().isoformat())

        db.add_entry(
            date=entry_date,
            food_item=data.get('food_item'),
            sodium_mg=float(data.get('sodium_mg', 0)),
            serving_size=data.get('serving_size', ''),
            meal_type=data.get('meal_type', ''),
            notes=data.get('notes', '')
        )

        return redirect('./')

    return render_template('add_entry.html',
                         today=get_current_date().isoformat(),
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url())

@app.route('/edit_entry/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    """Edit an existing sodium entry - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    if request.method == 'POST':
        data = request.form
        entry_date = data.get('date', get_current_date().isoformat())

        # Validate sodium value
        try:
            sodium_mg = float(data.get('sodium_mg', 0))
            if sodium_mg < 0 or sodium_mg > 50000:
                flash('Sodium must be between 0-50000 mg', 'error')
                return redirect(f"{get_sodium_url()}/edit_entry/{entry_id}")
        except ValueError:
            flash('Invalid sodium value', 'error')
            return redirect(f"{get_sodium_url()}/edit_entry/{entry_id}")

        success = db.update_entry(
            entry_id=entry_id,
            date=entry_date,
            food_item=data.get('food_item'),
            sodium_mg=sodium_mg,
            serving_size=data.get('serving_size', ''),
            meal_type=data.get('meal_type', ''),
            notes=data.get('notes', '')
        )

        if success:
            flash('Sodium entry updated successfully!', 'success')
            return redirect(f"{get_sodium_url()}/history")
        else:
            flash('Error updating entry', 'error')
            return redirect(f"{get_sodium_url()}/edit_entry/{entry_id}")

    # GET request - show form with existing data
    entry = db.get_entry_by_id(entry_id)
    if not entry:
        flash('Entry not found', 'error')
        return redirect(f"{get_sodium_url()}/history")

    return render_template('edit_entry.html',
                         entry=entry,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url())

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry_route(entry_id):
    """Delete a sodium entry - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    success = db.delete_entry(entry_id)

    if success:
        flash('Sodium entry deleted successfully!', 'success')
    else:
        flash('Error deleting entry', 'error')

    return redirect(f"{get_sodium_url()}/history")

@app.route('/history')
def history():
    """View sodium intake history - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    summaries = db.get_daily_summaries(limit=per_page, offset=offset)

    daily_summaries = []
    for summary in summaries:
        entry_date = summary['date']
        total_sodium = summary['total_sodium']
        entry_count = summary['entry_count']
        daily_goal = get_daily_goal(entry_date)
        percentage = (total_sodium / daily_goal * 100) if daily_goal > 0 else 0

        # Get all entries for this date
        entries = db.get_entries(date=entry_date)

        daily_summaries.append({
            'date': entry_date,
            'total_sodium': total_sodium,
            'entry_count': entry_count,
            'daily_goal': daily_goal,
            'percentage': round(percentage, 1),
            'entries': entries
        })

    return render_template('history.html',
                         daily_summaries=daily_summaries,
                         page=page,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Manage user settings - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    if request.method == 'POST':
        default_goal = request.form.get('default_daily_goal', 2300)
        alert_threshold = request.form.get('alert_threshold', 80)

        db.update_setting('default_daily_goal', str(default_goal))
        db.update_setting('alert_threshold', str(alert_threshold))

        return redirect('./')

    # Get current settings
    settings_data = db.get_all_settings()

    return render_template('settings.html',
                         settings=settings_data,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url())

@app.route('/api/daily_intake/<target_date>')
def api_daily_intake(target_date):
    """API endpoint to get daily intake"""
    intake = get_daily_intake(target_date)
    goal = get_daily_goal(target_date)

    return jsonify({
        'date': target_date,
        'intake': intake,
        'goal': goal,
        'percentage': round((intake / goal * 100) if goal > 0 else 0, 1)
    })

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """Delete a sodium entry - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    db.delete_entry(entry_id)
    return redirect('./')

# Redirect routes for inter-component navigation
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
    """Redirect to BP Monitor - environment-aware"""
    return redirect(get_bp_url())

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_database()

    # Use debug=False in production, True for development
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'

    # Read port from environment variable (for staging) or use default
    port = int(os.getenv('PORT', 5003))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')