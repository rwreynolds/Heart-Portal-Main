"""
Fluid-Tracker Component - Flask Application
Tracks daily fluid intake for heart failure patients
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime, date
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fluid-tracker-secret-key-change-in-production')

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'fluid_tracker.db')

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

def init_database():
    """Initialize the SQLite database"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create fluid_entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fluid_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            fluid_type TEXT NOT NULL,
            volume_ml INTEGER NOT NULL,
            container_size TEXT,
            time_consumed TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # Create daily_goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            target_ml INTEGER NOT NULL DEFAULT 2000,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # Create user_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT NOT NULL UNIQUE,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # Insert default settings
    cursor.execute('''
        INSERT OR IGNORE INTO user_settings (setting_name, setting_value, updated_at)
        VALUES ('default_daily_goal', '2000', ?)
    ''', (datetime.now().isoformat(),))

    cursor.execute('''
        INSERT OR IGNORE INTO user_settings (setting_name, setting_value, updated_at)
        VALUES ('alert_threshold', '80', ?)
    ''', (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

def get_daily_intake(target_date=None):
    """Get total fluid intake for a specific date"""
    if target_date is None:
        target_date = date.today().isoformat()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT SUM(volume_ml) FROM fluid_entries WHERE date = ?
    ''', (target_date,))

    result = cursor.fetchone()
    conn.close()

    return result[0] or 0

def get_daily_goal(target_date=None):
    """Get daily fluid goal for a specific date"""
    if target_date is None:
        target_date = date.today().isoformat()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Try to get specific goal for the date
    cursor.execute('''
        SELECT target_ml FROM daily_goals WHERE date = ?
    ''', (target_date,))

    result = cursor.fetchone()

    if result:
        conn.close()
        return result[0]

    # Fall back to default goal
    cursor.execute('''
        SELECT setting_value FROM user_settings WHERE setting_name = 'default_daily_goal'
    ''', )

    result = cursor.fetchone()
    conn.close()

    return int(result[0]) if result else 2000

@app.route('/')
def index():
    """Main fluid tracker dashboard"""
    today = date.today()
    today_str = today.isoformat()

    # Get today's intake
    daily_intake = get_daily_intake(today_str)
    daily_goal = get_daily_goal(today_str)

    # Calculate percentage
    percentage = (daily_intake / daily_goal * 100) if daily_goal > 0 else 0

    # Get recent entries
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM fluid_entries
        WHERE date = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (today_str,))

    entries = []
    for row in cursor.fetchall():
        entries.append({
            'id': row[0],
            'date': row[1],
            'fluid_type': row[2],
            'volume_ml': row[3],
            'container_size': row[4],
            'time_consumed': row[5],
            'notes': row[6],
            'created_at': row[7]
        })

    conn.close()

    return render_template('index.html',
                         daily_intake=daily_intake,
                         daily_goal=daily_goal,
                         percentage=round(percentage, 1),
                         entries=entries,
                         today=today_str,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url(),
                         sodium_url=get_sodium_url())

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    """Add a new fluid entry"""
    if request.method == 'POST':
        data = request.form
        entry_date = data.get('date', date.today().isoformat())

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO fluid_entries
            (date, fluid_type, volume_ml, container_size, time_consumed, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_date,
            data.get('fluid_type'),
            int(data.get('volume_ml', 0)),
            data.get('container_size'),
            data.get('time_consumed'),
            data.get('notes', ''),
            now,
            now
        ))

        conn.commit()
        conn.close()

        flash('Fluid entry added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_entry.html',
                         today=date.today().isoformat(),
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url(),
                         sodium_url=get_sodium_url())

@app.route('/history')
def history():
    """View fluid intake history"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT date, SUM(volume_ml) as total_volume, COUNT(*) as entry_count
        FROM fluid_entries
        GROUP BY date
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))

    daily_summaries = []
    for row in cursor.fetchall():
        entry_date = row[0]
        total_volume = row[1]
        entry_count = row[2]
        daily_goal = get_daily_goal(entry_date)
        percentage = (total_volume / daily_goal * 100) if daily_goal > 0 else 0

        daily_summaries.append({
            'date': entry_date,
            'total_volume': total_volume,
            'entry_count': entry_count,
            'daily_goal': daily_goal,
            'percentage': round(percentage, 1)
        })

    conn.close()

    return render_template('history.html',
                         daily_summaries=daily_summaries,
                         page=page,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url(),
                         sodium_url=get_sodium_url())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Manage user settings"""
    if request.method == 'POST':
        default_goal = request.form.get('default_daily_goal', 2000)
        alert_threshold = request.form.get('alert_threshold', 80)

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
            UPDATE user_settings
            SET setting_value = ?, updated_at = ?
            WHERE setting_name = 'default_daily_goal'
        ''', (default_goal, now))

        cursor.execute('''
            UPDATE user_settings
            SET setting_value = ?, updated_at = ?
            WHERE setting_name = 'alert_threshold'
        ''', (alert_threshold, now))

        conn.commit()
        conn.close()

        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))

    # Get current settings
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT setting_name, setting_value FROM user_settings')
    settings_data = dict(cursor.fetchall())
    conn.close()

    return render_template('settings.html',
                         settings=settings_data,
                         main_app_url=get_main_app_url(),
                         blog_url=get_blog_url(),
                         nutrition_url=get_nutrition_url(),
                         foodbase_url=get_foodbase_url(),
                         sodium_url=get_sodium_url())

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
    """Delete a fluid entry"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM fluid_entries WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()

    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('index'))

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
    app.run(debug=debug_mode, port=5004, host='0.0.0.0')