"""
Shared Authentication Module for Heart Portal
Provides user management, login/logout, and session handling
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, g
import os

# Database path for user authentication
AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

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
    """Get database connection"""
    db = sqlite3.connect(AUTH_DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_auth_db():
    """Initialize the authentication database"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    # Add is_admin column to existing tables if it doesn't exist
    try:
        db.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
        db.commit()
    except sqlite3.OperationalError:
        # Column already exists, which is fine
        pass

    # Create sessions table for session management
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    db.commit()
    db.close()

def hash_password(password):
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + pwd_hash.hex()

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    salt = password_hash[:32]
    pwd_hash = password_hash[32:]
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() == pwd_hash

def create_user(username, email, password):
    """Create a new user account"""
    db = get_db()
    try:
        password_hash = hash_password(password)
        cursor = db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        db.commit()
        return user_id
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return {'error': 'Username already exists'}
        elif 'email' in str(e):
            return {'error': 'Email already exists'}
        else:
            return {'error': 'User creation failed'}
    finally:
        db.close()

def authenticate_user(username, password):
    """Authenticate a user login"""
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ? AND is_active = 1',
        (username,)
    ).fetchone()
    db.close()

    if user and verify_password(password, user['password_hash']):
        return User(
            user['id'],
            user['username'],
            user['email'],
            user['password_hash'],
            user['created_at'],
            user['is_active'],
            user['is_admin']
        )
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE id = ? AND is_active = 1',
        (user_id,)
    ).fetchone()
    db.close()

    if user:
        return User(
            user['id'],
            user['username'],
            user['email'],
            user['password_hash'],
            user['created_at'],
            user['is_active'],
            user['is_admin']
        )
    return None

def create_session(user_id):
    """Create a user session"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=30)  # 30 day sessions

    db = get_db()
    db.execute(
        'INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
        (user_id, session_token, expires_at)
    )
    db.commit()
    db.close()

    return session_token

def get_user_from_session(session_token):
    """Get user from session token"""
    db = get_db()
    session_data = db.execute('''
        SELECT u.*, s.expires_at
        FROM users u
        JOIN user_sessions s ON u.id = s.user_id
        WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = 1
    ''', (session_token,)).fetchone()
    db.close()

    if session_data:
        return User(
            session_data['id'],
            session_data['username'],
            session_data['email'],
            session_data['password_hash'],
            session_data['created_at'],
            session_data['is_active'],
            session_data['is_admin']
        )
    return None

def invalidate_session(session_token):
    """Invalidate a user session (logout)"""
    db = get_db()
    db.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
    db.commit()
    db.close()

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    db = get_db()
    db.execute('DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP')
    db.commit()
    db.close()

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Staging mode bypass for testing
        if os.environ.get('STAGING_MODE', '').lower() == 'true' and os.environ.get('STAGING_AUTH_BYPASS', '').lower() == 'true':
            # Check if admin mode is enabled for staging
            is_admin = os.environ.get('STAGING_ADMIN_MODE', '').lower() == 'true'
            user_id = 998 if is_admin else 999
            username = 'staging_admin_user' if is_admin else 'staging_test_user'
            email = 'admin@staging.local' if is_admin else 'test@staging.local'

            # Create a fake user for staging tests
            fake_user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash='fake_hash',
                created_at=datetime.now().isoformat(),
                is_active=True,
                is_admin=is_admin
            )
            g.current_user = fake_user
            return f(*args, **kwargs)

        if 'session_token' not in session:
            return redirect(url_for('login'))

        user = get_user_from_session(session['session_token'])
        if not user:
            session.clear()
            return redirect(url_for('login'))

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get the current logged-in user"""
    # Staging mode bypass for testing
    if os.environ.get('STAGING_MODE', '').lower() == 'true' and os.environ.get('STAGING_AUTH_BYPASS', '').lower() == 'true':
        # Check if admin mode is enabled for staging
        is_admin = os.environ.get('STAGING_ADMIN_MODE', '').lower() == 'true'
        user_id = 998 if is_admin else 999
        username = 'staging_admin_user' if is_admin else 'staging_test_user'
        email = 'admin@staging.local' if is_admin else 'test@staging.local'

        # Create a fake user for staging tests
        fake_user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash='fake_hash',
            created_at=datetime.now().isoformat(),
            is_active=True,
            is_admin=is_admin
        )
        g.current_user = fake_user
        return fake_user

    if hasattr(g, 'current_user'):
        return g.current_user

    if 'session_token' in session:
        user = get_user_from_session(session['session_token'])
        if user:
            g.current_user = user
            return user

    return None

def is_user_logged_in():
    """Check if user is logged in"""
    return get_current_user() is not None

def make_user_admin(user_id):
    """Make a user an administrator"""
    db = get_db()
    db.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user_id,))
    db.commit()
    db.close()

def get_all_users():
    """Get all users (admin function)"""
    db = get_db()
    users = db.execute('SELECT id, username, email, created_at, is_active, is_admin FROM users').fetchall()
    db.close()
    return users

def deactivate_user(user_id):
    """Deactivate a user account"""
    db = get_db()
    db.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
    db.commit()
    db.close()

def activate_user(user_id):
    """Activate a user account"""
    db = get_db()
    db.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
    db.commit()
    db.close()

def remove_admin_privileges(user_id):
    """Remove admin privileges from a user"""
    db = get_db()
    db.execute('UPDATE users SET is_admin = 0 WHERE id = ?', (user_id,))
    db.commit()
    db.close()

def delete_user(user_id):
    """Delete a user account (use with caution)"""
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    db.close()