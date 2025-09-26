#!/usr/bin/env python3
"""
Script to create the first admin user for the Heart Portal system
"""

import os
import sys

# Add shared directory to path for authentication module
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))
from auth import init_auth_db, create_user, make_user_admin, get_all_users

def main():
    print("Creating first admin user for Heart Portal...")

    # Initialize the database
    init_auth_db()

    # Create admin user
    admin_username = "admin"
    admin_email = "admin@heartportal.local"
    admin_password = "HE080725rwr!"

    print(f"Creating user: {admin_username}")

    # Check if admin user already exists
    users = get_all_users()
    existing_admin = next((u for u in users if u['username'] == admin_username), None)

    if existing_admin:
        print(f"Admin user '{admin_username}' already exists!")
        if not existing_admin['is_admin']:
            print("Promoting existing user to admin...")
            make_user_admin(existing_admin['id'])
            print(f"✅ User '{admin_username}' promoted to admin successfully!")
        else:
            print("✅ User is already an admin!")
    else:
        # Create new admin user
        result = create_user(admin_username, admin_email, admin_password)

        if isinstance(result, dict) and 'error' in result:
            print(f"❌ Error creating user: {result['error']}")
            return

        # Get the newly created user
        users = get_all_users()
        new_user = next((u for u in users if u['username'] == admin_username), None)

        if new_user:
            # Make them admin
            make_user_admin(new_user['id'])
            print(f"✅ Admin user '{admin_username}' created successfully!")
        else:
            print("❌ Failed to find newly created user")
            return

    print("\nAdmin credentials:")
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print(f"Email: {admin_email}")
    print("\nYou can now log in and access the Admin Dashboard!")

if __name__ == "__main__":
    main()