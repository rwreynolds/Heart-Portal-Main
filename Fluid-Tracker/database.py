"""
Fluid Tracker Database Module
Handles fluid intake entries, daily goals, and user settings
Uses shared database module for SQLite/PostgreSQL support
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.database import create_db_config

# Initialize database configuration for fluid tracker
_db_config = create_db_config(
    app_name='fluid',
    db_name='heart_portal_staging_fluid',
    sqlite_path=os.path.join(os.path.dirname(__file__), 'database', 'fluid_tracker.db')
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


def init_fluid_database():
    """Initialize the fluid tracker database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fluid entries table
    autoincrement = _db_config.get_autoincrement_syntax()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS fluid_entries (
            id {autoincrement},
            date TEXT NOT NULL,
            beverage_name TEXT NOT NULL,
            volume_ml REAL NOT NULL,
            beverage_type TEXT,
            time_of_day TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fluid_date ON fluid_entries (date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_date ON daily_goals (date)')

    release_connection(conn)


def get_daily_total(date: str) -> float:
    """Get total fluid intake for a specific date"""
    conn = get_db_connection()

    query = 'SELECT SUM(volume_ml) as total FROM fluid_entries WHERE date = ?'
    cursor = _db_config.execute_query(conn, query, (date,))

    result = cursor.fetchone()
    total = result['total'] if result and result['total'] else 0.0

    release_connection(conn)
    return float(total)


def get_daily_goal(date: str) -> Optional[float]:
    """Get the daily fluid goal for a specific date"""
    conn = get_db_connection()

    query = 'SELECT target_ml FROM daily_goals WHERE date = ?'
    cursor = _db_config.execute_query(conn, query, (date,))

    result = cursor.fetchone()
    goal = result['target_ml'] if result else None

    release_connection(conn)
    return float(goal) if goal else None


def get_default_daily_goal() -> float:
    """Get the default daily fluid goal from settings"""
    conn = get_db_connection()

    query = "SELECT setting_value FROM user_settings WHERE setting_name = 'default_daily_goal'"
    cursor = _db_config.execute_query(conn, query)

    result = cursor.fetchone()
    default_goal = result['setting_value'] if result else '2000'

    release_connection(conn)
    return float(default_goal)


def get_entries(date: str = None, limit: int = 100) -> List[Dict]:
    """Get fluid entries, optionally filtered by date"""
    conn = get_db_connection()

    if date:
        query = '''
            SELECT * FROM fluid_entries
            WHERE date = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        cursor = _db_config.execute_query(conn, query, (date, limit))
    else:
        query = '''
            SELECT * FROM fluid_entries
            ORDER BY date DESC, created_at DESC
            LIMIT ?
        '''
        cursor = _db_config.execute_query(conn, query, (limit,))

    entries = [_db_config.normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return entries


def add_entry(date: str, beverage_name: str, volume_ml: float, beverage_type: str = '',
              time_of_day: str = '', notes: str = '') -> int:
    """Add a new fluid entry"""
    conn = get_db_connection()

    query = '''
        INSERT INTO fluid_entries (date, beverage_name, volume_ml, beverage_type, time_of_day, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    '''

    cursor = _db_config.execute_query(
        conn, query,
        (date, beverage_name, volume_ml, beverage_type, time_of_day, notes),
        use_dict_cursor=False
    )

    if _db_config.is_postgresql():
        cursor.execute('SELECT lastval()')
        entry_id = cursor.fetchone()[0]
    else:
        entry_id = cursor.lastrowid

    release_connection(conn)
    return entry_id


def update_entry(entry_id: int, beverage_name: str = None, volume_ml: float = None,
                beverage_type: str = None, time_of_day: str = None, notes: str = None) -> bool:
    """Update an existing fluid entry"""
    conn = get_db_connection()

    updates = []
    params = []

    if beverage_name is not None:
        updates.append('beverage_name = ?')
        params.append(beverage_name)
    if volume_ml is not None:
        updates.append('volume_ml = ?')
        params.append(volume_ml)
    if beverage_type is not None:
        updates.append('beverage_type = ?')
        params.append(beverage_type)
    if time_of_day is not None:
        updates.append('time_of_day = ?')
        params.append(time_of_day)
    if notes is not None:
        updates.append('notes = ?')
        params.append(notes)

    if not updates:
        release_connection(conn)
        return False

    params.append(entry_id)
    query = f"UPDATE fluid_entries SET {', '.join(updates)} WHERE id = ?"

    cursor = _db_config.execute_query(conn, query, tuple(params), use_dict_cursor=False)
    success = cursor.rowcount > 0

    release_connection(conn)
    return success


def delete_entry(entry_id: int) -> bool:
    """Delete a fluid entry"""
    conn = get_db_connection()

    query = 'DELETE FROM fluid_entries WHERE id = ?'
    cursor = _db_config.execute_query(conn, query, (entry_id,), use_dict_cursor=False)

    success = cursor.rowcount > 0
    release_connection(conn)
    return success


def set_daily_goal(date: str, target_ml: float) -> bool:
    """Set or update the daily fluid goal for a specific date"""
    conn = get_db_connection()

    # Try to insert first, if fails then update
    try:
        query = '''
            INSERT INTO daily_goals (date, target_ml, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        _db_config.execute_query(conn, query, (date, target_ml), use_dict_cursor=False)
        success = True
    except:
        # Update existing goal
        query = '''
            UPDATE daily_goals
            SET target_ml = ?, updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        '''
        cursor = _db_config.execute_query(conn, query, (target_ml, date), use_dict_cursor=False)
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
    """Get daily fluid summaries grouped by date"""
    conn = get_db_connection()

    query = '''
        SELECT date, SUM(volume_ml) as total_volume, COUNT(*) as entry_count
        FROM fluid_entries
        GROUP BY date
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    '''

    cursor = _db_config.execute_query(conn, query, (limit, offset))
    summaries = [_db_config.normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return summaries
