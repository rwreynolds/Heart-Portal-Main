"""
BP Monitor Database Module
Handles blood pressure entries, heart rate tracking, and user settings
Uses shared database module for SQLite/PostgreSQL support
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.database import create_db_config

# Initialize database configuration for BP monitor
_db_config = create_db_config(
    app_name='bp',
    db_name='heart_portal_staging_bp',
    sqlite_path=os.path.join(os.path.dirname(__file__), 'bp_monitor.db')
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


def init_bp_database():
    """Initialize the BP monitor database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # BP entries table
    autoincrement = _db_config.get_autoincrement_syntax()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS bp_entries (
            id {autoincrement},
            date TEXT NOT NULL,
            time TEXT,
            systolic INTEGER NOT NULL,
            diastolic INTEGER NOT NULL,
            heart_rate INTEGER,
            time_of_day TEXT DEFAULT 'morning',
            position TEXT DEFAULT 'sitting',
            arm TEXT DEFAULT 'left',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Settings table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS settings (
            id {autoincrement},
            bp_target_systolic INTEGER DEFAULT 120,
            bp_target_diastolic INTEGER DEFAULT 80,
            hr_target_min INTEGER DEFAULT 60,
            hr_target_max INTEGER DEFAULT 100,
            reminder_enabled INTEGER DEFAULT 1,
            reminder_time TEXT DEFAULT '08:00',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Check if time_of_day column exists (for migration from older databases)
    if _db_config.is_sqlite():
        check_cursor = cursor
        check_cursor.execute("PRAGMA table_info(bp_entries)")
        columns = [column[1] for column in check_cursor.fetchall()]
        if 'time_of_day' not in columns:
            cursor.execute("ALTER TABLE bp_entries ADD COLUMN time_of_day TEXT DEFAULT 'morning'")

    release_connection(conn)


# Database query functions
def get_settings(conn) -> Optional[Dict]:
    """Get user settings"""
    cursor = dict_cursor(conn)
    cursor.execute('SELECT * FROM settings ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    return normalize_row(result) if result else None


def get_today_entries(conn, today: str) -> List[Dict]:
    """Get today's BP entries"""
    query = 'SELECT * FROM bp_entries WHERE date = ? ORDER BY recorded_at DESC'
    cursor = _db_config.execute_query(conn, query, (today,))
    results = cursor.fetchall()
    return [normalize_row(row) for row in results]


def get_recent_entries(conn, week_ago: str, limit: int = 10) -> List[Dict]:
    """Get recent BP entries"""
    query = '''
        SELECT * FROM bp_entries
        WHERE date >= ?
        ORDER BY date DESC, recorded_at DESC
        LIMIT ?
    '''
    cursor = _db_config.execute_query(conn, query, (week_ago, limit))
    results = cursor.fetchall()
    return [normalize_row(row) for row in results]


def add_bp_entry(conn, date: str, time: str, systolic: int, diastolic: int,
                 heart_rate: Optional[int], time_of_day: str, position: str,
                 arm: str, notes: str = '') -> bool:
    """Add a new BP entry"""
    try:
        query = '''
            INSERT INTO bp_entries (date, time, systolic, diastolic, heart_rate,
                                    time_of_day, position, arm, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor = _db_config.execute_query(conn, query,
                                          (date, time, systolic, diastolic, heart_rate,
                                           time_of_day, position, arm, notes),
                                          use_dict_cursor=False)
        return True
    except Exception as e:
        print(f"Error adding BP entry: {e}")
        return False


def get_bp_history(conn, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Get paginated BP history"""
    query = '''
        SELECT * FROM bp_entries
        ORDER BY date DESC, recorded_at DESC
        LIMIT ? OFFSET ?
    '''
    cursor = _db_config.execute_query(conn, query, (limit, offset))
    results = cursor.fetchall()
    return [normalize_row(row) for row in results]


def get_total_entries_count(conn) -> int:
    """Get total count of BP entries"""
    query = 'SELECT COUNT(*) as count FROM bp_entries'
    cursor = _db_config.execute_query(conn, query)
    result = cursor.fetchone()
    return result['count'] if result else 0


def get_entries_since(conn, since_date: str) -> List[Dict]:
    """Get all entries since a specific date"""
    query = '''
        SELECT * FROM bp_entries
        WHERE date >= ?
        ORDER BY date ASC, recorded_at ASC
    '''
    cursor = _db_config.execute_query(conn, query, (since_date,))
    results = cursor.fetchall()
    return [normalize_row(row) for row in results]


def get_entry_by_id(conn, entry_id: int) -> Optional[Dict]:
    """Get a single BP entry by ID"""
    query = 'SELECT * FROM bp_entries WHERE id = ?'
    cursor = _db_config.execute_query(conn, query, (entry_id,))
    result = cursor.fetchone()
    return normalize_row(result) if result else None


def update_entry(conn, entry_id: int, date: str, time: str, systolic: int,
                diastolic: int, heart_rate: Optional[int], time_of_day: str,
                position: str, arm: str, notes: str = '') -> bool:
    """Update an existing BP entry"""
    try:
        query = '''
            UPDATE bp_entries SET
            date = ?, time = ?, systolic = ?, diastolic = ?,
            heart_rate = ?, time_of_day = ?, position = ?, arm = ?, notes = ?
            WHERE id = ?
        '''
        cursor = _db_config.execute_query(conn, query,
                                          (date, time, systolic, diastolic, heart_rate,
                                           time_of_day, position, arm, notes, entry_id),
                                          use_dict_cursor=False)
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating BP entry: {e}")
        return False


def delete_entry(conn, entry_id: int) -> bool:
    """Delete a BP entry"""
    try:
        query = 'DELETE FROM bp_entries WHERE id = ?'
        cursor = _db_config.execute_query(conn, query, (entry_id,), use_dict_cursor=False)
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting BP entry: {e}")
        return False


def update_settings(conn, bp_target_systolic: int, bp_target_diastolic: int,
                   hr_target_min: int, hr_target_max: int,
                   reminder_enabled: bool, reminder_time: str,
                   settings_id: int = None) -> bool:
    """Update user settings"""
    try:
        if settings_id:
            query = '''
                UPDATE settings SET
                bp_target_systolic = ?, bp_target_diastolic = ?,
                hr_target_min = ?, hr_target_max = ?,
                reminder_enabled = ?, reminder_time = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            cursor = _db_config.execute_query(conn, query,
                                              (bp_target_systolic, bp_target_diastolic,
                                               hr_target_min, hr_target_max,
                                               int(reminder_enabled), reminder_time, settings_id),
                                              use_dict_cursor=False)
        else:
            query = '''
                INSERT INTO settings (bp_target_systolic, bp_target_diastolic,
                                     hr_target_min, hr_target_max,
                                     reminder_enabled, reminder_time)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            cursor = _db_config.execute_query(conn, query,
                                              (bp_target_systolic, bp_target_diastolic,
                                               hr_target_min, hr_target_max,
                                               int(reminder_enabled), reminder_time),
                                              use_dict_cursor=False)
        return True
    except Exception as e:
        print(f"Error updating settings: {e}")
        return False
