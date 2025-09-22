#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import logging

app = Flask(__name__)
app.secret_key = 'weight-tracker-secret-key-2025'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database', 'weight_tracker.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def close_db_teardown(error):
    close_db()

def init_database():
    """Initialize the database with required tables"""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Weight entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weight_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                weight_lbs REAL NOT NULL,
                weight_kg REAL NOT NULL,
                time_of_day TEXT DEFAULT 'morning',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Weight goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weight_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_weight_lbs REAL NOT NULL,
                target_weight_kg REAL NOT NULL,
                goal_type TEXT DEFAULT 'maintain',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preferred_unit TEXT DEFAULT 'lbs',
                reminder_time TEXT DEFAULT '08:00',
                reminder_enabled INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default settings if none exist
        cursor.execute('SELECT COUNT(*) FROM user_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO user_settings (preferred_unit, reminder_time, reminder_enabled)
                VALUES ('lbs', '08:00', 1)
            ''')

        conn.commit()
        logger.info("Database initialized successfully")

def get_base_url():
    """Get the appropriate base URL based on environment"""
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        return 'http://localhost:3000'
    else:
        return 'https://heartfailureportal.com'

def lbs_to_kg(lbs):
    """Convert pounds to kilograms"""
    return round(lbs * 0.453592, 2)

def kg_to_lbs(kg):
    """Convert kilograms to pounds"""
    return round(kg * 2.20462, 2)

@app.route('/')
def index():
    """Weight tracking dashboard"""
    db = get_db()
    today = datetime.now().strftime('%Y-%m-%d')

    # Get user settings
    settings = db.execute('SELECT * FROM user_settings ORDER BY id DESC LIMIT 1').fetchone()
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    # Get today's weight entry
    today_entry = db.execute(
        'SELECT * FROM weight_entries WHERE date = ? ORDER BY created_at DESC LIMIT 1',
        (today,)
    ).fetchone()

    # Get recent entries (last 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_entries = db.execute(
        'SELECT * FROM weight_entries WHERE date >= ? ORDER BY date DESC, created_at DESC LIMIT 10',
        (week_ago,)
    ).fetchall()

    # Get current goal
    current_goal = db.execute(
        'SELECT * FROM weight_goals WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
    ).fetchone()

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
    """Add new weight entry"""
    if request.method == 'POST':
        date = request.form['date']
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

        db = get_db()
        db.execute('''
            INSERT INTO weight_entries (date, weight_lbs, weight_kg, time_of_day, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, weight_lbs, weight_kg, time_of_day, notes))
        db.commit()

        logger.info(f"Weight entry added: {weight_lbs}lbs/{weight_kg}kg on {date}")
        return redirect(url_for('index'))

    # Get user settings for default unit
    db = get_db()
    settings = db.execute('SELECT * FROM user_settings ORDER BY id DESC LIMIT 1').fetchone()
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    return render_template('add_entry.html',
                         preferred_unit=preferred_unit,
                         base_url=get_base_url())

@app.route('/history')
def history():
    """View weight history"""
    db = get_db()

    # Get all entries, paginated
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    entries = db.execute(
        'SELECT * FROM weight_entries ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()

    # Get total count for pagination
    total_entries = db.execute('SELECT COUNT(*) FROM weight_entries').fetchone()[0]

    # Get user settings
    settings = db.execute('SELECT * FROM user_settings ORDER BY id DESC LIMIT 1').fetchone()
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
    """User settings management"""
    db = get_db()

    if request.method == 'POST':
        preferred_unit = request.form['preferred_unit']
        reminder_time = request.form['reminder_time']
        reminder_enabled = 1 if 'reminder_enabled' in request.form else 0

        # Check if settings exist
        existing_settings = db.execute('SELECT id FROM user_settings LIMIT 1').fetchone()

        if existing_settings:
            db.execute('''
                UPDATE user_settings
                SET preferred_unit = ?, reminder_time = ?, reminder_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (preferred_unit, reminder_time, reminder_enabled, existing_settings['id']))
        else:
            db.execute('''
                INSERT INTO user_settings (preferred_unit, reminder_time, reminder_enabled)
                VALUES (?, ?, ?)
            ''', (preferred_unit, reminder_time, reminder_enabled))

        db.commit()
        logger.info("Settings updated successfully")
        return redirect(url_for('settings'))

    # Get current settings
    current_settings = db.execute('SELECT * FROM user_settings ORDER BY id DESC LIMIT 1').fetchone()

    return render_template('settings.html',
                         settings=current_settings,
                         base_url=get_base_url())

@app.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    """Set weight goal"""
    db = get_db()

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

        # Deactivate existing goals
        db.execute('UPDATE weight_goals SET is_active = 0')

        # Insert new goal
        db.execute('''
            INSERT INTO weight_goals (target_weight_lbs, target_weight_kg, goal_type, is_active)
            VALUES (?, ?, ?, 1)
        ''', (target_weight_lbs, target_weight_kg, goal_type))

        db.commit()
        logger.info(f"Weight goal set: {target_weight_lbs}lbs ({goal_type})")
        return redirect(url_for('index'))

    # Get user settings
    settings = db.execute('SELECT * FROM user_settings ORDER BY id DESC LIMIT 1').fetchone()
    preferred_unit = settings['preferred_unit'] if settings else 'lbs'

    # Get current goal
    current_goal = db.execute(
        'SELECT * FROM weight_goals WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
    ).fetchone()

    return render_template('set_goal.html',
                         preferred_unit=preferred_unit,
                         current_goal=current_goal,
                         base_url=get_base_url())

@app.route('/api/weight_data/<date>')
def api_weight_data(date):
    """API endpoint for weight data"""
    db = get_db()
    entry = db.execute(
        'SELECT * FROM weight_entries WHERE date = ? ORDER BY created_at DESC LIMIT 1',
        (date,)
    ).fetchone()

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
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/nutrition-database/')
    return redirect('http://localhost:5000')

@app.route('/redirect/foodbase')
def redirect_to_foodbase():
    """Redirect to Food-Base - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/food-base/')
    return redirect('http://localhost:5001')

@app.route('/redirect/sodium')
def redirect_to_sodium():
    """Redirect to Sodium Tracker - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/sodium-tracker/')
    return redirect('http://localhost:5003')

@app.route('/redirect/fluid')
def redirect_to_fluid():
    """Redirect to Fluid Tracker - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/fluid-tracker/')
    return redirect('http://localhost:5004')

@app.route('/redirect/weight')
def redirect_to_weight():
    """Redirect to Weight Tracker - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/weight-tracker/')
    return redirect('http://localhost:5005')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', base_url=get_base_url()), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', base_url=get_base_url()), 500

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=True)