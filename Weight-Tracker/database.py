"""
Weight Tracker Database Module
Handles weight entries, goals, and user settings
Uses shared database module for SQLite/PostgreSQL support
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.database import create_db_config

# Initialize database configuration for weight tracker
_db_config = create_db_config(
    app_name='weight',
    db_name='heart_portal_staging_weight',
    sqlite_path=os.path.join(os.path.dirname(__file__), 'database', 'weight_tracker.db')
)

# Convenience wrappers
def get_db_connection():
    """Get database connection"""
    return _db_config.get_connection()

def release_connection(conn):
    """Release database connection"""
    _db_config.release_connection(conn)

def dict_cursor(conn):
    """Get dictionary cursor"""
    return _db_config.dict_cursor(conn)

def normalize_row(row):
    """Normalize row data (handle datetime differences)"""
    return _db_config.normalize_row(row)


def init_weight_database():
    """Initialize the weight tracker database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Weight entries table
    autoincrement = _db_config.get_autoincrement_syntax()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS weight_entries (
            id {autoincrement},
            date TEXT NOT NULL,
            weight_lbs REAL NOT NULL,
            weight_kg REAL NOT NULL,
            time_of_day TEXT DEFAULT 'morning',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Weight goals table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS weight_goals (
            id {autoincrement},
            target_weight_lbs REAL NOT NULL,
            target_weight_kg REAL NOT NULL,
            goal_type TEXT DEFAULT 'maintain',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # User settings table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS user_settings (
            id {autoincrement},
            preferred_unit TEXT DEFAULT 'lbs',
            reminder_time TEXT DEFAULT '08:00',
            reminder_enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default settings if none exist
    check_query = 'SELECT COUNT(*) as count FROM user_settings'
    check_cursor = dict_cursor(conn)
    check_cursor.execute(check_query)
    result = check_cursor.fetchone()
    count = result['count'] if result else 0

    if count == 0:
        insert_query = '''
            INSERT INTO user_settings (preferred_unit, reminder_time, reminder_enabled)
            VALUES (?, ?, ?)
        '''
        _db_config.execute_query(conn, insert_query, ('lbs', '08:00', 1), use_dict_cursor=False)

    release_connection(conn)


# Database query functions
def get_user_settings(conn) -> Optional[Dict]:
    """Get user settings"""
    cursor = dict_cursor(conn)
    cursor.execute('SELECT * FROM user_settings ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    return normalize_row(result) if result else None


def get_today_entry(conn, today: str) -> Optional[Dict]:
    """Get today's weight entry"""
    query = 'SELECT * FROM weight_entries WHERE date = ? ORDER BY created_at DESC LIMIT 1'
    cursor = _db_config.execute_query(conn, query, (today,))
    result = cursor.fetchone()
    return normalize_row(result) if result else None


def get_recent_entries(conn, week_ago: str, limit: int = 10) -> List[Dict]:
    """Get recent weight entries"""
    query = '''
        SELECT * FROM weight_entries
        WHERE date >= ?
        ORDER BY date DESC, created_at DESC
        LIMIT ?
    '''
    cursor = _db_config.execute_query(conn, query, (week_ago, limit))
    results = cursor.fetchall()
    return [normalize_row(row) for row in results]


def get_current_goal(conn) -> Optional[Dict]:
    """Get current active goal"""
    query = 'SELECT * FROM weight_goals WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
    cursor = _db_config.execute_query(conn, query)
    result = cursor.fetchone()
    return normalize_row(result) if result else None


def add_weight_entry(conn, date: str, weight_lbs: float, weight_kg: float,
                     time_of_day: str, notes: str = '') -> bool:
    """Add a new weight entry"""
    try:
        query = '''
            INSERT INTO weight_entries (date, weight_lbs, weight_kg, time_of_day, notes)
            VALUES (?, ?, ?, ?, ?)
        '''
        cursor = _db_config.execute_query(conn, query,
                                          (date, weight_lbs, weight_kg, time_of_day, notes),
                                          use_dict_cursor=False)
        return True
    except Exception as e:
        print(f"Error adding weight entry: {e}")
        return False


def get_weight_history(conn, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Get paginated weight history"""
    query = '''
        SELECT * FROM weight_entries
        ORDER BY date DESC, created_at DESC
        LIMIT ? OFFSET ?
    '''
    cursor = _db_config.execute_query(conn, query, (limit, offset))
    results = cursor.fetchall()
    return [normalize_row(row) for row in results]


def get_total_entries_count(conn) -> int:
    """Get total count of weight entries"""
    query = 'SELECT COUNT(*) as count FROM weight_entries'
    cursor = _db_config.execute_query(conn, query)
    result = cursor.fetchone()
    return result['count'] if result else 0


def update_user_settings(conn, preferred_unit: str, reminder_time: str,
                        reminder_enabled: int, settings_id: int = None) -> bool:
    """Update user settings"""
    try:
        if settings_id:
            query = '''
                UPDATE user_settings
                SET preferred_unit = ?, reminder_time = ?, reminder_enabled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            cursor = _db_config.execute_query(conn, query,
                                              (preferred_unit, reminder_time, reminder_enabled, settings_id),
                                              use_dict_cursor=False)
        else:
            query = '''
                INSERT INTO user_settings (preferred_unit, reminder_time, reminder_enabled)
                VALUES (?, ?, ?)
            '''
            cursor = _db_config.execute_query(conn, query,
                                              (preferred_unit, reminder_time, reminder_enabled),
                                              use_dict_cursor=False)
        return True
    except Exception as e:
        print(f"Error updating settings: {e}")
        return False


def set_weight_goal(conn, target_weight_lbs: float, target_weight_kg: float,
                    goal_type: str) -> bool:
    """Set a new weight goal (deactivates existing goals)"""
    try:
        # Deactivate existing goals
        deactivate_query = 'UPDATE weight_goals SET is_active = 0'
        _db_config.execute_query(conn, deactivate_query, use_dict_cursor=False)

        # Insert new goal
        insert_query = '''
            INSERT INTO weight_goals (target_weight_lbs, target_weight_kg, goal_type, is_active)
            VALUES (?, ?, ?, 1)
        '''
        cursor = _db_config.execute_query(conn, insert_query,
                                          (target_weight_lbs, target_weight_kg, goal_type),
                                          use_dict_cursor=False)
        return True
    except Exception as e:
        print(f"Error setting weight goal: {e}")
        return False


def get_weight_entry_by_date(conn, date: str) -> Optional[Dict]:
    """Get weight entry for specific date"""
    query = 'SELECT * FROM weight_entries WHERE date = ? ORDER BY created_at DESC LIMIT 1'
    cursor = _db_config.execute_query(conn, query, (date,))
    result = cursor.fetchone()
    return normalize_row(result) if result else None


# Utility functions
def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms"""
    return round(lbs * 0.453592, 2)


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds"""
    return round(kg * 2.20462, 2)
