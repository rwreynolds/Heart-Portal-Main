import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, g
from urllib.parse import quote
import math
from dotenv import load_dotenv

# Load environment variables from both shared .env and app-specific .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # Shared .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # App-specific .env (overrides shared)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from session_config import configure_session
from auth import get_current_user
from url_helpers import get_base_url, get_bp_url, get_nutrition_url, get_foodbase_url, get_sodium_url, get_fluid_url, get_weight_url, get_main_app_url, get_blog_url

# Import database module
from database import (
    init_bp_database, get_db_connection, release_connection,
    get_settings, get_today_entries, get_recent_entries,
    add_bp_entry, get_bp_history, get_total_entries_count,
    get_entries_since, update_settings
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

configure_session(app)

# Configure Jinja to look in multiple template directories
from jinja2 import FileSystemLoader, ChoiceLoader
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

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

@app.context_processor
def inject_url_helpers():
    return {
        'get_main_app_url': get_main_app_url,
        'get_blog_url': get_blog_url,
        'get_nutrition_url': get_nutrition_url,
        'get_foodbase_url': get_foodbase_url,
        'get_sodium_url': get_sodium_url,
        'get_fluid_url': get_fluid_url,
        'get_weight_url': get_weight_url,
        'get_bp_url': get_bp_url,
        'get_current_user': get_current_user
    }

@app.route('/')
def index():
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    conn = get_db()

    # Get today's entries
    today = datetime.now().strftime('%Y-%m-%d')
    today_entries = get_today_entries(conn, today)

    # Get recent entries (last 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_entries = get_recent_entries(conn, week_ago, limit=10)

    # Get settings
    settings = get_settings(conn)

    # Calculate averages and trends
    stats = calculate_stats(conn)
    trends = calculate_trends(conn)

    return render_template('index.html',
                         today_entries=today_entries,
                         recent_entries=recent_entries,
                         settings=settings,
                         stats=stats,
                         trends=trends,
                         today=today)

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        systolic = int(request.form['systolic'])
        diastolic = int(request.form['diastolic'])
        heart_rate = request.form['heart_rate']
        time_of_day = request.form.get('time_of_day', 'morning')
        position = request.form['position']
        arm = request.form['arm']
        notes = request.form['notes']

        # Validate blood pressure values
        if systolic < 50 or systolic > 300:
            flash('Systolic pressure must be between 50-300 mmHg', 'error')
            return redirect(url_for('add_entry'))

        if diastolic < 30 or diastolic > 200:
            flash('Diastolic pressure must be between 30-200 mmHg', 'error')
            return redirect(url_for('add_entry'))

        if systolic <= diastolic:
            flash('Systolic pressure must be higher than diastolic pressure', 'error')
            return redirect(url_for('add_entry'))

        # Validate heart rate if provided
        if heart_rate and (int(heart_rate) < 30 or int(heart_rate) > 250):
            flash('Heart rate must be between 30-250 bpm', 'error')
            return redirect(url_for('add_entry'))

        conn = get_db()
        success = add_bp_entry(conn, date, time, systolic, diastolic,
                               int(heart_rate) if heart_rate else None,
                               time_of_day, position, arm, notes)

        if success:
            flash('Blood pressure entry recorded successfully!', 'success')
        return redirect(get_bp_url())

    # GET request - show form
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M')

    return render_template('add_entry.html', today=today, current_time=current_time)

@app.route('/history')
def history():
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    conn = get_db()

    # Get total count
    total_entries = get_total_entries_count(conn)

    # Get entries for current page
    entries = get_bp_history(conn, limit=per_page, offset=offset)

    # Calculate statistics
    stats = calculate_stats(conn)

    return render_template('history.html',
                         entries=entries,
                         total_entries=total_entries,
                         page=page,
                         per_page=per_page,
                         stats=stats)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    conn = get_db()

    if request.method == 'POST':
        bp_target_systolic = int(request.form['bp_target_systolic'])
        bp_target_diastolic = int(request.form['bp_target_diastolic'])
        hr_target_min = int(request.form['hr_target_min'])
        hr_target_max = int(request.form['hr_target_max'])
        reminder_enabled = 'reminder_enabled' in request.form
        reminder_time = request.form['reminder_time']

        # Check if settings exist
        existing = get_settings(conn)
        settings_id = existing['id'] if existing else None

        success = update_settings(conn, bp_target_systolic, bp_target_diastolic,
                                 hr_target_min, hr_target_max,
                                 reminder_enabled, reminder_time, settings_id)

        if success:
            flash('Settings saved successfully!', 'success')
        return redirect(get_bp_url())

    # GET request
    settings = get_settings(conn)
    return render_template('settings.html', settings=settings)

@app.route('/analytics')
def analytics():
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={quote(request.url, safe='')}")

    conn = get_db()

    # Get data for last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    entries = get_entries_since(conn, thirty_days_ago)

    # Prepare data for charts
    chart_data = prepare_chart_data(entries)
    stats = calculate_stats(conn)
    categories = categorize_readings(entries)

    return render_template('analytics.html',
                         chart_data=chart_data,
                         stats=stats,
                         categories=categories,
                         entries=entries)

# Redirect routes for reverse proxy compatibility
@app.route('/redirect/nutrition')
def redirect_nutrition():
    return redirect(get_nutrition_url())

@app.route('/redirect/foodbase')
def redirect_foodbase():
    return redirect(get_foodbase_url())

@app.route('/redirect/sodium')
def redirect_sodium():
    return redirect(get_sodium_url())

@app.route('/redirect/fluid')
def redirect_fluid():
    return redirect(get_fluid_url())

@app.route('/redirect/weight')
def redirect_weight():
    return redirect(get_weight_url())

def calculate_stats(conn):
    """Calculate various statistics from blood pressure data"""
    stats = {}

    # Last 7 days averages
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_entries = get_entries_since(conn, week_ago)

    if week_entries:
        stats['avg_systolic_week'] = sum(e['systolic'] for e in week_entries) / len(week_entries)
        stats['avg_diastolic_week'] = sum(e['diastolic'] for e in week_entries) / len(week_entries)
        hr_entries = [e['heart_rate'] for e in week_entries if e['heart_rate']]
        if hr_entries:
            stats['avg_heart_rate_week'] = sum(hr_entries) / len(hr_entries)

    # Last 30 days averages
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    month_entries = get_entries_since(conn, month_ago)

    if month_entries:
        stats['avg_systolic_month'] = sum(e['systolic'] for e in month_entries) / len(month_entries)
        stats['avg_diastolic_month'] = sum(e['diastolic'] for e in month_entries) / len(month_entries)
        hr_entries = [e['heart_rate'] for e in month_entries if e['heart_rate']]
        if hr_entries:
            stats['avg_heart_rate_month'] = sum(hr_entries) / len(hr_entries)

    return stats

def calculate_trends(conn):
    """Calculate trends in blood pressure readings"""
    trends = {}

    # Get last 14 days of data
    fourteen_days_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    entries = get_entries_since(conn, fourteen_days_ago)

    if len(entries) >= 4:  # Need at least 4 readings for trend
        # Split into first and second half
        mid_point = len(entries) // 2
        first_half = entries[:mid_point]
        second_half = entries[mid_point:]

        # Calculate averages for each half
        first_sys = sum(e['systolic'] for e in first_half) / len(first_half)
        second_sys = sum(e['systolic'] for e in second_half) / len(second_half)

        first_dia = sum(e['diastolic'] for e in first_half) / len(first_half)
        second_dia = sum(e['diastolic'] for e in second_half) / len(second_half)

        # Determine trends
        sys_change = second_sys - first_sys
        dia_change = second_dia - first_dia

        if abs(sys_change) < 3:
            trends['systolic'] = 'stable'
        elif sys_change > 0:
            trends['systolic'] = 'increasing'
        else:
            trends['systolic'] = 'decreasing'

        if abs(dia_change) < 2:
            trends['diastolic'] = 'stable'
        elif dia_change > 0:
            trends['diastolic'] = 'increasing'
        else:
            trends['diastolic'] = 'decreasing'

    return trends

def prepare_chart_data(entries):
    """Prepare data for JavaScript charts"""
    chart_data = {
        'dates': [],
        'systolic': [],
        'diastolic': [],
        'heart_rate': []
    }

    for entry in entries:
        chart_data['dates'].append(f"{entry['date']} {entry['time'] or '00:00'}")
        chart_data['systolic'].append(entry['systolic'])
        chart_data['diastolic'].append(entry['diastolic'])
        chart_data['heart_rate'].append(entry['heart_rate'] if entry['heart_rate'] else None)

    return chart_data

def categorize_readings(entries):
    """Categorize blood pressure readings according to AHA guidelines"""
    categories = {
        'normal': 0,        # <120 and <80
        'elevated': 0,      # 120-129 and <80
        'stage1': 0,        # 130-139 or 80-89
        'stage2': 0,        # 140-179 or 90-119
        'crisis': 0         # >=180 or >=120
    }

    for entry in entries:
        sys = entry['systolic']
        dia = entry['diastolic']

        if sys >= 180 or dia >= 120:
            categories['crisis'] += 1
        elif sys >= 140 or dia >= 90:
            categories['stage2'] += 1
        elif sys >= 130 or dia >= 80:
            categories['stage1'] += 1
        elif sys >= 120 and dia < 80:
            categories['elevated'] += 1
        else:
            categories['normal'] += 1

    return categories

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5006))
    app.run(host='0.0.0.0', port=port, debug=True)