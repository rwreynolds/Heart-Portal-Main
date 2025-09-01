"""
Database package for Food-Base component
Handles all database operations and models
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_database(app):
    """Initialize database with Flask app"""
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_path = os.path.join(basedir, 'food_base.db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return db

def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print(f"📊 Database tables created successfully")

def get_database_info():
    """Get database information"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_path = os.path.join(basedir, 'food_base.db')
    
    return {
        'path': database_path,
        'exists': os.path.exists(database_path),
        'size': os.path.getsize(database_path) if os.path.exists(database_path) else 0
    }