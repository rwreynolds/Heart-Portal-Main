"""
Sodium Tracker Database Module
Handles sodium intake entries, daily goals, and user settings
Uses shared database module for SQLite/PostgreSQL support
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.database import create_db_config

# Initialize database configuration for sodium tracker
_db_config = create_db_config(
    app_name='sodium',
    db_name='heart_portal_staging_sodium',
    sqlite_path=os.path.join(os.path.dirname(__file__), 'database', 'sodium_tracker.db')
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


def init_sodium_database():
    """Initialize the sodium tracker database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sodium entries table
    autoincrement = _db_config.get_autoincrement_syntax()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS sodium_entries (
            id {autoincrement},
            date TEXT NOT NULL,
            food_item TEXT NOT NULL,
            sodium_mg REAL NOT NULL,
            serving_size TEXT,
            meal_type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Daily goals table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS daily_goals (
            id {autoincrement},
            date TEXT NOT NULL UNIQUE,
            target_mg REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User settings table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS user_settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sodium_date ON sodium_entries (date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_date ON daily_goals (date)')

    release_connection(conn)


def get_daily_total(date: str) -> float:
    """Get total sodium intake for a specific date"""
    conn = get_db_connection()

    query = 'SELECT SUM(sodium_mg) as total FROM sodium_entries WHERE date = ?'
    cursor = _db_config.execute_query(conn, query, (date,))

    result = cursor.fetchone()
    total = result['total'] if result and result['total'] else 0.0

    release_connection(conn)
    return float(total)


def get_daily_goal(date: str) -> Optional[float]:
    """Get the daily sodium goal for a specific date"""
    conn = get_db_connection()

    query = 'SELECT target_mg FROM daily_goals WHERE date = ?'
    cursor = _db_config.execute_query(conn, query, (date,))

    result = cursor.fetchone()
    goal = result['target_mg'] if result else None

    release_connection(conn)
    return float(goal) if goal else None


def get_default_daily_goal() -> float:
    """Get the default daily sodium goal from settings"""
    conn = get_db_connection()

    query = "SELECT setting_value FROM user_settings WHERE setting_name = 'default_daily_goal'"
    cursor = _db_config.execute_query(conn, query)

    result = cursor.fetchone()
    default_goal = result['setting_value'] if result else '2000'

    release_connection(conn)
    return float(default_goal)


def get_entries(date: str = None, limit: int = 100) -> List[Dict]:
    """Get sodium entries, optionally filtered by date"""
    conn = get_db_connection()

    if date:
        query = '''
            SELECT * FROM sodium_entries
            WHERE date = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        cursor = _db_config.execute_query(conn, query, (date, limit))
    else:
        query = '''
            SELECT * FROM sodium_entries
            ORDER BY date DESC, created_at DESC
            LIMIT ?
        '''
        cursor = _db_config.execute_query(conn, query, (limit,))

    entries = [_db_config.normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return entries


def get_entry_by_id(entry_id: int) -> Optional[Dict]:
    """Get a single sodium entry by ID"""
    conn = get_db_connection()

    query = 'SELECT * FROM sodium_entries WHERE id = ?'
    cursor = _db_config.execute_query(conn, query, (entry_id,))

    result = cursor.fetchone()
    entry = _db_config.normalize_row(result) if result else None

    release_connection(conn)
    return entry


def add_entry(date: str, food_item: str, sodium_mg: float, serving_size: str = '',
              meal_type: str = '', notes: str = '') -> int:
    """Add a new sodium entry"""
    conn = get_db_connection()

    query = '''
        INSERT INTO sodium_entries (date, food_item, sodium_mg, serving_size, meal_type, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    '''

    cursor = _db_config.execute_query(
        conn, query,
        (date, food_item, sodium_mg, serving_size, meal_type, notes),
        use_dict_cursor=False
    )

    if _db_config.is_postgresql():
        cursor.execute('SELECT lastval()')
        entry_id = cursor.fetchone()[0]
    else:
        entry_id = cursor.lastrowid

    release_connection(conn)
    return entry_id


def update_entry(entry_id: int, date: str, food_item: str, sodium_mg: float,
                serving_size: str = '', meal_type: str = '', notes: str = '') -> bool:
    """Update an existing sodium entry"""
    conn = get_db_connection()

    try:
        query = '''
            UPDATE sodium_entries SET
            date = ?, food_item = ?, sodium_mg = ?, serving_size = ?,
            meal_type = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        cursor = _db_config.execute_query(conn, query,
                                          (date, food_item, sodium_mg, serving_size,
                                           meal_type, notes, entry_id),
                                          use_dict_cursor=False)
        success = cursor.rowcount > 0
        release_connection(conn)
        return success
    except Exception as e:
        print(f"Error updating sodium entry: {e}")
        release_connection(conn)
        return False


def delete_entry(entry_id: int) -> bool:
    """Delete a sodium entry"""
    conn = get_db_connection()

    query = 'DELETE FROM sodium_entries WHERE id = ?'
    cursor = _db_config.execute_query(conn, query, (entry_id,), use_dict_cursor=False)

    success = cursor.rowcount > 0
    release_connection(conn)
    return success


def set_daily_goal(date: str, target_mg: float) -> bool:
    """Set or update the daily sodium goal for a specific date"""
    conn = get_db_connection()

    # Try to insert first, if fails then update
    try:
        query = '''
            INSERT INTO daily_goals (date, target_mg, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        _db_config.execute_query(conn, query, (date, target_mg), use_dict_cursor=False)
        success = True
    except:
        # Update existing goal
        query = '''
            UPDATE daily_goals
            SET target_mg = ?, updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        '''
        cursor = _db_config.execute_query(conn, query, (target_mg, date), use_dict_cursor=False)
        success = cursor.rowcount > 0

    release_connection(conn)
    return success


def get_all_settings() -> Dict[str, str]:
    """Get all user settings"""
    conn = get_db_connection()

    query = 'SELECT setting_name, setting_value FROM user_settings'
    cursor = _db_config.execute_query(conn, query)

    settings = {row['setting_name']: row['setting_value'] for row in cursor.fetchall()}
    release_connection(conn)
    return settings


def update_setting(setting_name: str, setting_value: str) -> bool:
    """Update or insert a user setting"""
    conn = get_db_connection()

    # Try to update first
    query = '''
        UPDATE user_settings
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE setting_name = ?
    '''
    cursor = _db_config.execute_query(conn, query, (setting_value, setting_name), use_dict_cursor=False)

    if cursor.rowcount == 0:
        # Insert new setting
        query = '''
            INSERT INTO user_settings (setting_name, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        _db_config.execute_query(conn, query, (setting_name, setting_value), use_dict_cursor=False)

    release_connection(conn)
    return True


def get_daily_summaries(limit: int = 50, offset: int = 0) -> list:
    """Get daily sodium summaries grouped by date"""
    conn = get_db_connection()

    query = '''
        SELECT date, SUM(sodium_mg) as total_sodium, COUNT(*) as entry_count
        FROM sodium_entries
        GROUP BY date
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    '''

    cursor = _db_config.execute_query(conn, query, (limit, offset))
    summaries = [_db_config.normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return summaries
