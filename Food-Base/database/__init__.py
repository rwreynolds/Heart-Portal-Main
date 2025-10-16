"""
Database package for Food-Base component
Handles all database operations and models
Supports both SQLite and PostgreSQL via environment variables
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

# Check which database to use
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite').lower()

def init_database(app):
    """
    Initialize database with Flask app

    Database type is controlled by DATABASE_TYPE environment variable:
    - 'sqlite' (default): Uses local SQLite database
    - 'postgresql': Uses PostgreSQL database from DATABASE_URL
    """
    if DATABASE_TYPE == 'postgresql':
        # PostgreSQL configuration
        database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://heartportal:password@localhost:5432/heart_portal_staging_food'
        )
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"📊 Using PostgreSQL database")
    else:
        # SQLite configuration (default)
        basedir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(basedir, 'food_base.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
        print(f"📊 Using SQLite database at {database_path}")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before using
        'pool_recycle': 300,    # Recycle connections after 5 minutes
    }

    # Initialize database
    db.init_app(app)

    return db

def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        db_type = "PostgreSQL" if DATABASE_TYPE == 'postgresql' else "SQLite"
        print(f"📊 {db_type} database tables created successfully")

def get_database_info():
    """Get database information"""
    if DATABASE_TYPE == 'postgresql':
        database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://heartportal:password@localhost:5432/heart_portal_staging_food'
        )
        return {
            'type': 'postgresql',
            'url': database_url.replace(database_url.split('@')[0].split('//')[1], '***'),  # Hide credentials
            'exists': True  # Assume exists if configured
        }
    else:
        basedir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(basedir, 'food_base.db')
        return {
            'type': 'sqlite',
            'path': database_path,
            'exists': os.path.exists(database_path),
            'size': os.path.getsize(database_path) if os.path.exists(database_path) else 0
        }

def is_postgresql():
    """Check if using PostgreSQL"""
    return DATABASE_TYPE == 'postgresql'

def is_sqlite():
    """Check if using SQLite"""
    return DATABASE_TYPE == 'sqlite'