"""
Shared Authentication Module for Heart Portal
Provides user management, login/logout, and session handling with PostgreSQL and SQLite
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, g
import os

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL_USERS')

# Determine database type from URL
IS_SQLITE = DATABASE_URL and DATABASE_URL.startswith('sqlite:///')
IS_POSTGRES = DATABASE_URL and DATABASE_URL.startswith('postgresql://')

# Import appropriate database driver
if IS_SQLITE:
    import sqlite3
elif IS_POSTGRES:
    import psycopg2
    import psycopg2.extras

class User:
    """User model for authentication"""
    def __init__(self, id, username, email, password_hash, created_at, is_active=True, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.is_active = is_active
        self.is_admin = is_admin
        self.is_authenticated = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)

def get_db():
    """Get database connection - supports both SQLite and PostgreSQL"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL_USERS environment variable not set")

    if IS_SQLITE:
        # Extract file path from sqlite:///path format
        db_path = DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    elif IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        raise ValueError(f"Unsupported database URL format: {DATABASE_URL}")

def init_auth_db():
    """Initialize the authentication database - supports both SQLite and PostgreSQL"""
    conn = get_db()
    cursor = conn.cursor()

    if IS_SQLITE:
        # SQLite syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                is_admin INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')
    else:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
        ''')

    # Create index on session_token for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token)
    ''')

    # Create index on expires_at for cleanup queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_session_expires ON user_sessions(expires_at)
    ''')

    conn.commit()
    cursor.close()
    conn.close()

def hash_password(password):
    """Hash a password with PBKDF2 and salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + pwd_hash.hex()

def verify_password(password, password_hash):
    """Verify a password against its hash using PBKDF2"""
    salt = password_hash[:32]
    pwd_hash = password_hash[32:]
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() == pwd_hash

def create_user(username, email, password, is_admin=False):
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (username, email, password_hash, is_admin))

        user_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return user_id
    except psycopg2.IntegrityError as e:
        conn.rollback()
        cursor.close()
        conn.close()
        if 'username' in str(e):
            raise ValueError("Username already exists")
        elif 'email' in str(e):
            raise ValueError("Email already exists")
        else:
            raise ValueError("User creation failed")

def authenticate_user(username, password):
    """Authenticate a user and return User object if successful"""
    conn = get_db()
    cursor = conn.cursor()

    if IS_SQLITE:
        cursor.execute('''
            SELECT id, username, email, password_hash, created_at, is_active, is_admin
            FROM users
            WHERE username = ? AND is_active = 1
        ''', (username,))
    else:
        cursor.execute('''
            SELECT id, username, email, password_hash, created_at, is_active, is_admin
            FROM users
            WHERE username = %s AND is_active = TRUE
        ''', (username,))

    user_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_row and verify_password(password, user_row['password_hash']):
        return User(
            id=user_row['id'],
            username=user_row['username'],
            email=user_row['email'],
            password_hash=user_row['password_hash'],
            created_at=user_row['created_at'],
            is_active=user_row['is_active'],
            is_admin=user_row['is_admin']
        )

    return None

def get_user_by_id(user_id):
    """Get a user by their ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, email, password_hash, created_at, is_active, is_admin
        FROM users
        WHERE id = %s
    ''', (user_id,))

    user_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_row:
        return User(
            id=user_row['id'],
            username=user_row['username'],
            email=user_row['email'],
            password_hash=user_row['password_hash'],
            created_at=user_row['created_at'],
            is_active=user_row['is_active'],
            is_admin=user_row['is_admin']
        )

    return None

def get_user_by_username(username):
    """Get a user by their username"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, email, password_hash, created_at, is_active, is_admin
        FROM users
        WHERE username = %s
    ''', (username,))

    user_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_row:
        return User(
            id=user_row['id'],
            username=user_row['username'],
            email=user_row['email'],
            password_hash=user_row['password_hash'],
            created_at=user_row['created_at'],
            is_active=user_row['is_active'],
            is_admin=user_row['is_admin']
        )

    return None

def get_all_users():
    """Get all users"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, email, password_hash, created_at, is_active, is_admin
        FROM users
        ORDER BY created_at DESC
    ''')

    users = []
    for row in cursor.fetchall():
        users.append(User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            created_at=row['created_at'],
            is_active=row['is_active'],
            is_admin=row['is_admin']
        ))

    cursor.close()
    conn.close()
    return users

def update_user(user_id, **kwargs):
    """Update user fields"""
    conn = get_db()
    cursor = conn.cursor()

    allowed_fields = {'username', 'email', 'is_active', 'is_admin'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not updates:
        cursor.close()
        conn.close()
        return False

    set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [user_id]

    cursor.execute(f'''
        UPDATE users
        SET {set_clause}
        WHERE id = %s
    ''', values)

    success = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return success

def update_password(user_id, new_password):
    """Update a user's password"""
    conn = get_db()
    cursor = conn.cursor()

    password_hash = hash_password(new_password)

    cursor.execute('''
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
    ''', (password_hash, user_id))

    success = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return success

def delete_user(user_id):
    """Delete a user (soft delete by setting is_active to False)"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users
        SET is_active = FALSE
        WHERE id = %s
    ''', (user_id,))

    success = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return success

def create_session(user_id, ip_address=None, user_agent=None, duration_days=30):
    """Create a new session for a user"""
    conn = get_db()
    cursor = conn.cursor()

    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=duration_days)

    cursor.execute('''
        INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING session_token
    ''', (user_id, session_token, expires_at, ip_address, user_agent))

    token = cursor.fetchone()['session_token']
    conn.commit()
    cursor.close()
    conn.close()
    return token

def get_session(session_token):
    """Get a session by token"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, expires_at
        FROM user_sessions
        WHERE session_token = %s AND expires_at > NOW()
    ''', (session_token,))

    session_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if session_row:
        return {
            'user_id': session_row['user_id'],
            'expires_at': session_row['expires_at']
        }

    return None

def delete_session(session_token):
    """Delete a session (logout)"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM user_sessions
        WHERE session_token = %s
    ''', (session_token,))

    success = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return success

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM user_sessions
        WHERE expires_at < NOW()
    ''')

    count = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return count

def get_current_user():
    """Get the currently logged-in user from session"""
    if 'user_id' not in session:
        return None

    return get_user_by_id(session['user_id'])

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
