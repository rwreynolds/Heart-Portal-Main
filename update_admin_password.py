#!/usr/bin/env python3
"""
Script to update the admin user password
Run this script on the server to change the admin password
"""

import sys
import os
import secrets
import string

# Add the shared directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from auth import init_auth_db, get_all_users, hash_password, get_db

def generate_strong_password(length=16):
    """Generate a cryptographically strong password"""
    # Use a mix of letters, numbers, and symbols
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def update_admin_password(username="admin", new_password=None):
    """Update admin user password"""

    # Initialize database connection
    init_auth_db()

    # Generate strong password if none provided
    if new_password is None:
        new_password = generate_strong_password()

    print(f"Updating password for user: {username}")

    # Get database connection
    db = get_db()

    # Check if user exists
    user = db.execute(
        'SELECT id, username, is_admin FROM users WHERE username = ?',
        (username,)
    ).fetchone()

    if not user:
        print(f"❌ User '{username}' not found!")
        return False

    if not user['is_admin']:
        print(f"❌ User '{username}' is not an admin!")
        return False

    # Hash the new password
    password_hash = hash_password(new_password)

    # Update the password
    db.execute(
        'UPDATE users SET password_hash = ? WHERE username = ?',
        (password_hash, username)
    )
    db.commit()

    print(f"✅ Password updated successfully for admin user: {username}")
    print(f"🔐 New password: {new_password}")
    print(f"⚠️  Save this password securely!")

    return True

if __name__ == "__main__":
    print("========================================")
    print("🔐 Admin Password Update Script")
    print("========================================")
    print()

    # Check for command line arguments
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
        print("Using provided password...")
    else:
        print("Generating new secure password...")
        new_password = None

    success = update_admin_password(new_password=new_password)

    if success:
        print()
        print("✅ Admin password updated successfully!")
        print("🌐 You can now login at: https://heartfailureportal.com/login")
        print()
    else:
        print()
        print("❌ Failed to update admin password")
        sys.exit(1)