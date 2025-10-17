#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates all Heart Portal application data from SQLite to PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql

# Database password
PG_PASSWORD = "HE080725rwr!"
PG_HOST = "127.0.0.1"
PG_USER = "heartportal"

def migrate_blog_manager():
    """Migrate Blog-Manager from SQLite to PostgreSQL"""
    print("\n=== Migrating Blog-Manager ===")

    # Connect to SQLite
    sqlite_path = "/opt/heart-portal-staging/Blog-Manager/database/blog.db"
    if not os.path.exists(sqlite_path):
        print(f"⚠️  SQLite database not found: {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        user=PG_USER,
        password=PG_PASSWORD,
        database="heart_portal_staging_blog"
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Create tables - match the exact schema from Blog-Manager/database.py
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            visibility TEXT DEFAULT 'private',
            slug TEXT UNIQUE,
            excerpt TEXT,
            featured_image TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            reviewer_id INTEGER,
            review_notes TEXT
        )
    """)

    # Create indexes
    pg_cur.execute('CREATE INDEX IF NOT EXISTS idx_posts_status ON blog_posts (status)')
    pg_cur.execute('CREATE INDEX IF NOT EXISTS idx_posts_visibility ON blog_posts (visibility)')
    pg_cur.execute('CREATE INDEX IF NOT EXISTS idx_posts_author ON blog_posts (author_id)')
    pg_cur.execute('CREATE INDEX IF NOT EXISTS idx_posts_published ON blog_posts (published_at)')

    # Copy data - use actual column names from SQLite schema
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("""
        SELECT title, content, author_id, author_name, status, visibility, slug,
               excerpt, featured_image, tags, created_at, updated_at, published_at,
               reviewer_id, review_notes
        FROM blog_posts
    """)
    rows = sqlite_cur.fetchall()

    for row in rows:
        pg_cur.execute("""
            INSERT INTO blog_posts
            (title, content, author_id, author_name, status, visibility, slug,
             excerpt, featured_image, tags, created_at, updated_at, published_at,
             reviewer_id, review_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, row)

    print(f"✅ Migrated {len(rows)} blog posts")

    sqlite_conn.close()
    pg_conn.close()

def migrate_sodium_tracker():
    """Migrate Sodium-Tracker from SQLite to PostgreSQL"""
    print("\n=== Migrating Sodium-Tracker ===")

    sqlite_path = "/opt/heart-portal-staging/Sodium-Tracker/database/sodium_tracker.db"
    if not os.path.exists(sqlite_path):
        print(f"⚠️  SQLite database not found: {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = psycopg2.connect(
        host=PG_HOST,
        user=PG_USER,
        password=PG_PASSWORD,
        database="heart_portal_staging_sodium"
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Create tables
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS sodium_entries (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            food_name TEXT NOT NULL,
            sodium_mg INTEGER NOT NULL,
            notes TEXT
        )
    """)

    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id SERIAL PRIMARY KEY,
            daily_limit INTEGER DEFAULT 2000
        )
    """)

    # Copy sodium entries
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT date, food_name, sodium_mg, notes FROM sodium_entries")
    rows = sqlite_cur.fetchall()

    for row in rows:
        pg_cur.execute(
            "INSERT INTO sodium_entries (date, food_name, sodium_mg, notes) VALUES (%s, %s, %s, %s)",
            (row[0], row[1], row[2], row[3])
        )

    print(f"✅ Migrated {len(rows)} sodium entries")

    # Copy settings
    sqlite_cur.execute("SELECT daily_limit FROM user_settings LIMIT 1")
    settings = sqlite_cur.fetchone()
    if settings:
        pg_cur.execute("INSERT INTO user_settings (daily_limit) VALUES (%s)", (settings[0],))
        print(f"✅ Migrated user settings (daily limit: {settings[0]})")

    sqlite_conn.close()
    pg_conn.close()

def migrate_fluid_tracker():
    """Migrate Fluid-Tracker from SQLite to PostgreSQL"""
    print("\n=== Migrating Fluid-Tracker ===")

    sqlite_path = "/opt/heart-portal-staging/Fluid-Tracker/database/fluid_tracker.db"
    if not os.path.exists(sqlite_path):
        print(f"⚠️  SQLite database not found: {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = psycopg2.connect(
        host=PG_HOST,
        user=PG_USER,
        password=PG_PASSWORD,
        database="heart_portal_staging_fluid"
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Create tables
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS fluid_entries (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            fluid_oz REAL NOT NULL,
            fluid_type TEXT,
            notes TEXT
        )
    """)

    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id SERIAL PRIMARY KEY,
            daily_goal_oz REAL DEFAULT 64.0
        )
    """)

    # Copy fluid entries
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT date, fluid_oz, fluid_type, notes FROM fluid_entries")
    rows = sqlite_cur.fetchall()

    for row in rows:
        pg_cur.execute(
            "INSERT INTO fluid_entries (date, fluid_oz, fluid_type, notes) VALUES (%s, %s, %s, %s)",
            (row[0], row[1], row[2], row[3])
        )

    print(f"✅ Migrated {len(rows)} fluid entries")

    # Copy settings
    sqlite_cur.execute("SELECT daily_goal_oz FROM user_settings LIMIT 1")
    settings = sqlite_cur.fetchone()
    if settings:
        pg_cur.execute("INSERT INTO user_settings (daily_goal_oz) VALUES (%s)", (settings[0],))
        print(f"✅ Migrated user settings (daily goal: {settings[0]} oz)")

    sqlite_conn.close()
    pg_conn.close()

def migrate_weight_tracker():
    """Migrate Weight-Tracker from SQLite to PostgreSQL"""
    print("\n=== Migrating Weight-Tracker ===")

    sqlite_path = "/opt/heart-portal-staging/Weight-Tracker/database/weight_tracker.db"
    if not os.path.exists(sqlite_path):
        print(f"⚠️  SQLite database not found: {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = psycopg2.connect(
        host=PG_HOST,
        user=PG_USER,
        password=PG_PASSWORD,
        database="heart_portal_staging_weight"
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Create tables
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS weight_entries (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            weight_lbs REAL NOT NULL,
            notes TEXT,
            UNIQUE(date)
        )
    """)

    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS weight_goals (
            id SERIAL PRIMARY KEY,
            goal_weight_lbs REAL,
            target_date TEXT
        )
    """)

    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id SERIAL PRIMARY KEY,
            unit TEXT DEFAULT 'lbs'
        )
    """)

    # Copy weight entries
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT date, weight_lbs, notes FROM weight_entries")
    rows = sqlite_cur.fetchall()

    for row in rows:
        try:
            pg_cur.execute(
                "INSERT INTO weight_entries (date, weight_lbs, notes) VALUES (%s, %s, %s) ON CONFLICT (date) DO NOTHING",
                (row[0], row[1], row[2])
            )
        except:
            pass  # Skip duplicates

    print(f"✅ Migrated {len(rows)} weight entries")

    # Copy goals
    sqlite_cur.execute("SELECT goal_weight_lbs, target_date FROM weight_goals LIMIT 1")
    goal = sqlite_cur.fetchone()
    if goal:
        pg_cur.execute("INSERT INTO weight_goals (goal_weight_lbs, target_date) VALUES (%s, %s)", (goal[0], goal[1]))
        print(f"✅ Migrated weight goal: {goal[0]} lbs by {goal[1]}")

    # Copy settings
    sqlite_cur.execute("SELECT unit FROM user_settings LIMIT 1")
    settings = sqlite_cur.fetchone()
    if settings:
        pg_cur.execute("INSERT INTO user_settings (unit) VALUES (%s)", (settings[0],))
        print(f"✅ Migrated user settings (unit: {settings[0]})")

    sqlite_conn.close()
    pg_conn.close()

def migrate_bp_monitor():
    """Migrate BP-Monitor from SQLite to PostgreSQL"""
    print("\n=== Migrating BP-Monitor ===")

    sqlite_path = "/opt/heart-portal-staging/BP-Monitor/bp_monitor.db"
    if not os.path.exists(sqlite_path):
        print(f"⚠️  SQLite database not found: {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = psycopg2.connect(
        host=PG_HOST,
        user=PG_USER,
        password=PG_PASSWORD,
        database="heart_portal_staging_bp"
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Create tables
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS bp_entries (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            systolic INTEGER NOT NULL,
            diastolic INTEGER NOT NULL,
            pulse INTEGER,
            time_of_day TEXT,
            notes TEXT
        )
    """)

    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            systolic_target INTEGER DEFAULT 120,
            diastolic_target INTEGER DEFAULT 80
        )
    """)

    # Copy BP entries
    sqlite_cur = sqlite_conn.cursor()
    # Check if time_of_day column exists
    sqlite_cur.execute("PRAGMA table_info(bp_entries)")
    columns = [col[1] for col in sqlite_cur.fetchall()]

    if 'time_of_day' in columns:
        sqlite_cur.execute("SELECT date, systolic, diastolic, pulse, time_of_day, notes FROM bp_entries")
    else:
        sqlite_cur.execute("SELECT date, systolic, diastolic, pulse, notes FROM bp_entries")

    rows = sqlite_cur.fetchall()

    for row in rows:
        if 'time_of_day' in columns:
            pg_cur.execute(
                "INSERT INTO bp_entries (date, systolic, diastolic, pulse, time_of_day, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                (row[0], row[1], row[2], row[3], row[4], row[5])
            )
        else:
            pg_cur.execute(
                "INSERT INTO bp_entries (date, systolic, diastolic, pulse, notes) VALUES (%s, %s, %s, %s, %s)",
                (row[0], row[1], row[2], row[3], row[4])
            )

    print(f"✅ Migrated {len(rows)} BP entries")

    # Copy settings
    sqlite_cur.execute("SELECT systolic_target, diastolic_target FROM settings LIMIT 1")
    settings = sqlite_cur.fetchone()
    if settings:
        pg_cur.execute("INSERT INTO settings (systolic_target, diastolic_target) VALUES (%s, %s)", (settings[0], settings[1]))
        print(f"✅ Migrated settings (targets: {settings[0]}/{settings[1]})")

    sqlite_conn.close()
    pg_conn.close()

def main():
    print("=" * 60)
    print("Heart Portal: SQLite to PostgreSQL Migration")
    print("=" * 60)

    try:
        migrate_blog_manager()
        migrate_sodium_tracker()
        migrate_fluid_tracker()
        migrate_weight_tracker()
        migrate_bp_monitor()

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
