"""
Shared Database Module for Heart Portal Applications
Provides unified database abstraction layer supporting both SQLite and PostgreSQL
Each application configures its database path/URL via environment variables
"""

import os
from datetime import datetime
from typing import Dict, Optional, Any
from urllib.parse import urlparse, unquote

# Check which database to use
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite').lower()

# Import appropriate database driver
if DATABASE_TYPE == 'postgresql':
    import psycopg2
    import psycopg2.extras
    from psycopg2 import pool
else:
    import sqlite3


class DatabaseConfig:
    """Database configuration for each application"""

    def __init__(self, app_name: str, db_name: str, sqlite_path: str = None):
        """
        Initialize database configuration

        Args:
            app_name: Name of the application (e.g., 'blog', 'sodium', 'fluid')
            db_name: PostgreSQL database name (e.g., 'heart_portal_staging_blog')
            sqlite_path: Path to SQLite database file (optional, defaults to ./database/{app_name}.db)
        """
        self.app_name = app_name
        self.db_name = db_name
        self.database_type = DATABASE_TYPE

        if DATABASE_TYPE == 'postgresql':
            # PostgreSQL configuration
            self.database_url = os.getenv(
                'DATABASE_URL',
                f'postgresql://heartportal:password@localhost:5432/{db_name}'
            )
            self.connection_pool = None
        else:
            # SQLite configuration
            if sqlite_path:
                self.database_path = sqlite_path
            else:
                # Default to ./database/{app_name}.db relative to caller
                import inspect
                caller_frame = inspect.stack()[1]
                caller_dir = os.path.dirname(os.path.abspath(caller_frame.filename))
                self.database_path = os.path.join(caller_dir, 'database', f'{app_name}.db')

    def init_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        if DATABASE_TYPE == 'postgresql' and self.connection_pool is None:
            # Parse and decode the DATABASE_URL to handle URL-encoded passwords
            parsed_url = urlparse(self.database_url)
            decoded_password = unquote(parsed_url.password) if parsed_url.password else None

            # Reconstruct the URL with decoded password
            if decoded_password and decoded_password != parsed_url.password:
                decoded_url = f"{parsed_url.scheme}://{parsed_url.username}:{decoded_password}@{parsed_url.hostname}:{parsed_url.port or 5432}{parsed_url.path}"
            else:
                decoded_url = self.database_url

            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,  # min and max connections
                decoded_url
            )

    def get_connection(self):
        """Get database connection (PostgreSQL from pool, SQLite direct)"""
        if DATABASE_TYPE == 'postgresql':
            self.init_connection_pool()
            conn = self.connection_pool.getconn()
            conn.autocommit = True
            return conn
        else:
            # SQLite connection with optimized settings
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            conn = sqlite3.connect(self.database_path, timeout=30.0, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
            conn.execute('PRAGMA busy_timeout=30000')  # 30 second timeout
            conn.isolation_level = None  # Autocommit mode
            return conn

    def release_connection(self, conn):
        """Release connection (return to pool or close)"""
        if DATABASE_TYPE == 'postgresql':
            if self.connection_pool:
                self.connection_pool.putconn(conn)
        else:
            conn.close()

    def dict_cursor(self, conn):
        """Get cursor that returns rows as dictionaries"""
        if DATABASE_TYPE == 'postgresql':
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            return conn.cursor()

    def execute_query(self, conn, query: str, params: tuple = None, use_dict_cursor: bool = True):
        """
        Execute a query with automatic parameter conversion for PostgreSQL vs SQLite

        Args:
            conn: Database connection
            query: SQL query (use ? for parameters, will auto-convert to %s for PostgreSQL)
            params: Query parameters
            use_dict_cursor: Whether to return results as dictionaries

        Returns:
            Cursor object
        """
        # Convert ? placeholders to %s for PostgreSQL
        if DATABASE_TYPE == 'postgresql' and query:
            query = query.replace('?', '%s')

        cursor = self.dict_cursor(conn) if use_dict_cursor else conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        return cursor

    def normalize_row(self, row) -> Optional[Dict]:
        """
        Convert database row to dictionary with normalized datetime fields
        PostgreSQL returns datetime objects, SQLite returns strings
        """
        if row is None:
            return None

        result = dict(row)

        # Convert datetime objects to ISO format strings for PostgreSQL
        if DATABASE_TYPE == 'postgresql':
            for key, value in result.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()

        return result

    def get_placeholder(self, index: int = None) -> str:
        """
        Get appropriate parameter placeholder for database type

        Args:
            index: Parameter index (1-based for PostgreSQL numbered params)

        Returns:
            '?' for SQLite, '%s' for PostgreSQL
        """
        if DATABASE_TYPE == 'postgresql':
            return f'${index}' if index else '%s'
        return '?'

    def get_autoincrement_syntax(self) -> str:
        """Get appropriate auto-increment column syntax"""
        if DATABASE_TYPE == 'postgresql':
            return 'SERIAL PRIMARY KEY'
        return 'INTEGER PRIMARY KEY AUTOINCREMENT'

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL"""
        return DATABASE_TYPE == 'postgresql'

    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return DATABASE_TYPE == 'sqlite'


# Convenience functions for simple use cases
def create_db_config(app_name: str, db_name: str = None, sqlite_path: str = None) -> DatabaseConfig:
    """
    Create database configuration

    Args:
        app_name: Application name (e.g., 'blog', 'sodium')
        db_name: PostgreSQL database name (defaults to heart_portal_staging_{app_name})
        sqlite_path: SQLite database path (optional)

    Returns:
        DatabaseConfig instance
    """
    if db_name is None:
        db_name = f'heart_portal_staging_{app_name}'

    return DatabaseConfig(app_name, db_name, sqlite_path)


# Module-level helper for getting database type
def get_database_type() -> str:
    """Get current database type (sqlite or postgresql)"""
    return DATABASE_TYPE


def is_postgresql() -> bool:
    """Check if using PostgreSQL"""
    return DATABASE_TYPE == 'postgresql'


def is_sqlite() -> bool:
    """Check if using SQLite"""
    return DATABASE_TYPE == 'sqlite'
