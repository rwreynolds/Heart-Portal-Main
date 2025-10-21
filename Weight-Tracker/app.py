#!/usr/bin/env python3

import os
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure Flask app with shared templates
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Add shared directory to path for authentication module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from auth import get_current_user

# Import shared URL helpers
from url_helpers import (
    get_main_app_url, get_blog_url, get_nutrition_url, get_foodbase_url,
    get_sodium_url, get_fluid_url, get_weight_url, get_bp_url
)

# Import database module
from database import (
    init_weight_database, get_db_connection, release_connection,
    get_user_settings, get_today_entry, get_recent_entries, get_current_goal,
    add_weight_entry, get_weight_history, get_total_entries_count,
    update_user_settings, set_weight_goal, get_weight_entry_by_date,
    lbs_to_kg, kg_to_lbs
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

# Configure Jinja to look in multiple template directories
from jinja2 import FileSystemLoader, ChoiceLoader
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection management using Flask g object
def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        release_connection(db)

@app.teardown_appcontext
def close_db_teardown(error):
    """Teardown function to close database"""
    close_db()

def get_base_url():
    """Get the appropriate base URL based on environment"""
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        return 'http://localhost:3000'
    else:
        return 'https://heartfailureportal.com'

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

@app.route('/')
def index():
    """Weight tracking dashboard - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')

    # Get user settings
    settings = get_user_settings(conn)
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    # Get today's weight entry
    today_entry = get_today_entry(conn, today)

    # Get recent entries (last 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_entries = get_recent_entries(conn, week_ago, limit=10)

    # Get current goal
    current_goal = get_current_goal(conn)

    # Calculate trend (last 7 days)
    weight_trend = None
    if len(recent_entries) >= 2:
        latest_weight = recent_entries[0]['weight_lbs']
        week_ago_weight = recent_entries[-1]['weight_lbs']
        weight_change = latest_weight - week_ago_weight

        if abs(weight_change) < 0.5:
            weight_trend = 'stable'
        elif weight_change > 0:
            weight_trend = 'increasing'
        else:
            weight_trend = 'decreasing'

    return render_template('index.html',
                         today_entry=today_entry,
                         recent_entries=recent_entries,
                         current_goal=current_goal,
                         weight_trend=weight_trend,
                         preferred_unit=preferred_unit,
                         base_url=get_base_url())

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    """Add new weight entry - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    if request.method == 'POST':
        entry_date = request.form['date']
        weight_input = float(request.form['weight'])
        unit = request.form['unit']
        time_of_day = request.form['time_of_day']
        notes = request.form.get('notes', '')

        # Convert to both units for storage
        if unit == 'lbs':
            weight_lbs = weight_input
            weight_kg = lbs_to_kg(weight_input)
        else:
            weight_kg = weight_input
            weight_lbs = kg_to_lbs(weight_input)

        conn = get_db()
        success = add_weight_entry(conn, entry_date, weight_lbs, weight_kg, time_of_day, notes)

        if success:
            logger.info(f"Weight entry added: {weight_lbs}lbs/{weight_kg}kg on {entry_date}")
        return redirect('./')

    # Get user settings for default unit
    conn = get_db()
    settings = get_user_settings(conn)
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    return render_template('add_entry.html',
                         preferred_unit=preferred_unit,
                         today=date.today().isoformat(),
                         base_url=get_base_url())

@app.route('/history')
def history():
    """View weight history - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    conn = get_db()

    # Get all entries, paginated
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    entries = get_weight_history(conn, limit=per_page, offset=offset)

    # Get total count for pagination
    total_entries = get_total_entries_count(conn)

    # Get user settings
    settings = get_user_settings(conn)
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    return render_template('history.html',
                         entries=entries,
                         page=page,
                         per_page=per_page,
                         total_entries=total_entries,
                         preferred_unit=preferred_unit,
                         base_url=get_base_url())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """User settings management - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    conn = get_db()

    if request.method == 'POST':
        preferred_unit = request.form['preferred_unit']
        reminder_time = request.form['reminder_time']
        reminder_enabled = 1 if 'reminder_enabled' in request.form else 0

        # Check if settings exist
        existing_settings = get_user_settings(conn)
        settings_id = existing_settings['id'] if existing_settings else None

        success = update_user_settings(conn, preferred_unit, reminder_time,
                                       reminder_enabled, settings_id)

        if success:
            logger.info("Settings updated successfully")
        return redirect('./')

    # Get current settings
    current_settings = get_user_settings(conn)

    return render_template('settings.html',
                         settings=current_settings,
                         base_url=get_base_url())

@app.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    """Set weight goal"""
    conn = get_db()

    if request.method == 'POST':
        target_weight = float(request.form['target_weight'])
        unit = request.form['unit']
        goal_type = request.form['goal_type']

        # Convert to both units
        if unit == 'lbs':
            target_weight_lbs = target_weight
            target_weight_kg = lbs_to_kg(target_weight)
        else:
            target_weight_kg = target_weight
            target_weight_lbs = kg_to_lbs(target_weight)

        success = set_weight_goal(conn, target_weight_lbs, target_weight_kg, goal_type)

        if success:
            logger.info(f"Weight goal set: {target_weight_lbs}lbs ({goal_type})")
        return redirect('./')

    # Get user settings
    settings = get_user_settings(conn)
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    # Get current goal
    current_goal = get_current_goal(conn)

    return render_template('set_goal.html',
                         preferred_unit=preferred_unit,
                         current_goal=current_goal,
                         base_url=get_base_url())

@app.route('/api/weight_data/<date>')
def api_weight_data(date):
    """API endpoint for weight data"""
    conn = get_db()
    entry = get_weight_entry_by_date(conn, date)

    if entry:
        return jsonify({
            'date': entry['date'],
            'weight_lbs': entry['weight_lbs'],
            'weight_kg': entry['weight_kg'],
            'time_of_day': entry['time_of_day'],
            'notes': entry['notes']
        })
    else:
        return jsonify({'error': 'No weight entry found for this date'}), 404

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

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', base_url=get_base_url()), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', base_url=get_base_url()), 500

if __name__ == '__main__':
    init_weight_database()
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=True)