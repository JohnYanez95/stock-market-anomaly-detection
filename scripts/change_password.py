#!/usr/bin/env python3
"""
Password Change Utility

Simple script to change user passwords without regenerating all security settings.

Usage:
    python scripts/change_password.py
    python scripts/change_password.py --user admin --password newpass123
    python scripts/change_password.py --user admin  # Will prompt for password
"""

import argparse
import sys
import os
import json
import getpass
from pathlib import Path

# Add monitoring to path
sys.path.append('monitoring')

def load_env_file():
    """Load and parse .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ No .env file found")
        return None, None
    
    env_lines = []
    env_vars = {}
    
    with open(env_path, 'r') as f:
        env_lines = f.readlines()
    
    for line in env_lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value
            os.environ[key] = value
    
    return env_lines, env_vars

def save_env_file(env_lines, updates):
    """Save updated environment file"""
    # Remove lines for keys we're updating
    filtered_lines = []
    for line in env_lines:
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
            key = line_stripped.split('=', 1)[0]
            if key not in updates:
                filtered_lines.append(line)
        else:
            filtered_lines.append(line)
    
    # Add updated values
    for key, value in updates.items():
        filtered_lines.append(f'{key}={value}\n')
    
    # Write back
    with open('.env', 'w') as f:
        f.writelines(filtered_lines)

def change_password(username, new_password):
    """Change password for a specific user"""
    from auth import DashboardAuth
    
    # Load current environment
    env_lines, env_vars = load_env_file()
    if env_lines is None:
        return False
    
    auth = DashboardAuth()
    
    # Get current users
    users_json = env_vars.get('DASHBOARD_USERS')
    if users_json:
        try:
            users = json.loads(users_json)
        except json.JSONDecodeError:
            print(f"❌ Invalid DASHBOARD_USERS JSON in .env file")
            return False
    else:
        users = {}
    
    # Check if user exists
    if username not in users:
        print(f"❌ User '{username}' not found")
        print(f"Available users: {list(users.keys())}")
        return False
    
    # Generate new hash
    new_hash, new_salt = auth.hash_password(new_password)
    
    # Update user data
    users[username]['password_hash'] = new_hash
    users[username]['salt'] = new_salt
    
    # Prepare updates
    updates = {
        'DASHBOARD_USERS': json.dumps(users)
    }
    
    # If this is the admin user, also update simple auth
    if username == 'admin':
        updates['DASHBOARD_USERNAME'] = 'admin'
        updates['DASHBOARD_PASSWORD'] = new_password
    
    # Save changes
    save_env_file(env_lines, updates)
    
    print(f"✅ Password changed for user '{username}'")
    
    # Verify the change works
    if auth.authenticate_user(username, new_password):
        print(f"✅ Password change verified - authentication works")
        return True
    else:
        print(f"❌ Password change verification failed")
        return False

def main():
    parser = argparse.ArgumentParser(description='Change user password')
    parser.add_argument('--user', default='admin', help='Username to change password for')
    parser.add_argument('--password', help='New password (will prompt if not provided)')
    parser.add_argument('--list-users', action='store_true', help='List available users')
    
    args = parser.parse_args()
    
    # Load environment
    env_lines, env_vars = load_env_file()
    if env_lines is None:
        sys.exit(1)
    
    # List users if requested
    if args.list_users:
        users_json = env_vars.get('DASHBOARD_USERS')
        if users_json:
            try:
                users = json.loads(users_json)
                print("Available users:")
                for username, user_data in users.items():
                    role = user_data.get('role', 'unknown')
                    created = user_data.get('created', 'unknown')
                    print(f"  - {username} (role: {role}, created: {created})")
            except json.JSONDecodeError:
                print("❌ Invalid DASHBOARD_USERS JSON in .env file")
        else:
            print("No users found in DASHBOARD_USERS")
        return
    
    # Get password
    password = args.password
    if not password:
        password = getpass.getpass(f"Enter new password for {args.user}: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords don't match")
            sys.exit(1)
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        sys.exit(1)
    
    # Change password
    if change_password(args.user, password):
        print(f"\n🔒 Password successfully changed for '{args.user}'")
        print("\nTo use the new password:")
        print("  1. Restart the dashboard if it's running")
        print("  2. Login with the new credentials")
    else:
        print(f"\n❌ Failed to change password for '{args.user}'")
        sys.exit(1)

if __name__ == '__main__':
    main()