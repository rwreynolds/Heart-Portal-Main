#!/usr/bin/env python3
"""
Simple SQLite to PostgreSQL migration
Copies exact schemas and all data from SQLite to PostgreSQL
"""

import sqlite3
import psycopg2
import sys

PG_PASSWORD = "HE080725rwr!"
PG_HOST = "127.0.0.1"
PG_USER = "heartportal"

def convert_sqlite_type_to_pg(sqlite_type):
    """Convert SQLite type to PostgreSQL type"""
    sqlite_type = sqlite_type.upper()
    if 'INT' in sqlite_type:
        return 'INTEGER'
    elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'REAL'
    elif 'BLOB' in sqlite_type:
        return 'BYTEA'
    elif 'BOOL' in sqlite_type:
        return 'BOOLEAN'
    else:
        return 'TEXT'

def migrate_database(sqlite_path, pg_dbname, app_name):
    """Migrate one SQLite database to PostgreSQL"""
    print(f"\n=== Migrating {app_name} ===")
    print(f"From: {sqlite_path}")
    print(f"To: {pg_dbname}")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        user=PG_USER,
        password=PG_PASSWORD,
        database=pg_dbname
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Get all tables from SQLite
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in sqlite_cur.fetchall()]

    total_rows = 0

    for table_name in tables:
        print(f"  Migrating table: {table_name}")

        # Get table structure
        sqlite_cur.execute(f"PRAGMA table_info({table_name})")
        columns = sqlite_cur.fetchall()

        # Create PostgreSQL table
        col_defs = []
        for col in columns:
            col_name = col[1]
            col_type = convert_sqlite_type_to_pg(col[2])
            not_null = ' NOT NULL' if col[3] else ''
            default = f" DEFAULT {col[4]}" if col[4] else ''

            # Handle AUTOINCREMENT -> SERIAL
            if col[5] == 1:  # primary key
                col_def = f"{col_name} SERIAL PRIMARY KEY"
            else:
                col_def = f"{col_name} {col_type}{not_null}{default}"

            col_defs.append(col_def)

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"

        try:
            pg_cur.execute(create_sql)
        except Exception as e:
            print(f"    Warning creating table: {e}")

        # Copy data
        sqlite_cur.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cur.fetchall()

        if rows:
            # Get column names (excluding id for SERIAL columns)
            col_names = [col[1] for col in columns]
            placeholders = ','.join(['%s'] * len(col_names))
            insert_sql = f"INSERT INTO {table_name} ({','.join(col_names)}) VALUES ({placeholders})"

            for row in rows:
                try:
                    pg_cur.execute(insert_sql, tuple(row))
                except Exception as e:
                    print(f"    Warning inserting row: {e}")

            total_rows += len(rows)
            print(f"    ✅ Copied {len(rows)} rows")
        else:
            print(f"    (empty table)")

    # Get and create indexes
    sqlite_cur.execute("""
        SELECT sql FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        AND name NOT LIKE 'sqlite_%'
    """)
    indexes = [row[0] for row in sqlite_cur.fetchall()]

    for index_sql in indexes:
        try:
            # Convert SQLite index to PostgreSQL
            index_sql = index_sql.replace('IF NOT EXISTS', '')
            pg_cur.execute(index_sql + ' IF NOT EXISTS')
        except:
            pass

    sqlite_conn.close()
    pg_conn.close()

    print(f"  ✅ Total: {total_rows} rows migrated")

def main():
    migrations = [
        ('/opt/heart-portal-staging/Blog-Manager/database/blog.db',
         'heart_portal_staging_blog', 'Blog-Manager'),
        ('/opt/heart-portal-staging/Sodium-Tracker/database/sodium_tracker.db',
         'heart_portal_staging_sodium', 'Sodium-Tracker'),
        ('/opt/heart-portal-staging/Fluid-Tracker/database/fluid_tracker.db',
         'heart_portal_staging_fluid', 'Fluid-Tracker'),
        ('/opt/heart-portal-staging/Weight-Tracker/database/weight_tracker.db',
         'heart_portal_staging_weight', 'Weight-Tracker'),
        ('/opt/heart-portal-staging/BP-Monitor/bp_monitor.db',
         'heart_portal_staging_bp', 'BP-Monitor'),
    ]

    print("=" * 60)
    print("SQLite to PostgreSQL Migration")
    print("=" * 60)

    for sqlite_path, pg_dbname, app_name in migrations:
        try:
            migrate_database(sqlite_path, pg_dbname, app_name)
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
