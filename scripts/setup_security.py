#!/usr/bin/env python3
"""
Security Setup Script for Streamlit Dashboard

This script helps configure security settings for the dashboard including:
- User account creation with secure password hashing
- SSL certificate generation
- Environment configuration
- Security validation

Usage:
    python scripts/setup_security.py --help
"""

import argparse
import os
import sys
import json
import secrets
import subprocess
from pathlib import Path
import hashlib
from datetime import datetime

# Add monitoring to path for auth module
sys.path.append('monitoring')
from auth import DashboardAuth

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_user_account(username, password=None, role='user'):
    """Create a user account with secure password hashing"""
    auth = DashboardAuth()
    
    if not password:
        password = generate_secure_password()
        print(f"Generated password for {username}: {password}")
    
    hashed_password, salt = auth.hash_password(password)
    
    return {
        'password_hash': hashed_password,
        'salt': salt,
        'role': role,
        'created': datetime.now().isoformat()
    }

def setup_users(args):
    """Setup user accounts"""
    print("🔐 Setting up user accounts...")
    
    users = {}
    
    # Admin user
    admin_password = args.admin_password or generate_secure_password()
    users['admin'] = create_user_account('admin', admin_password, 'admin')
    
    if not args.admin_password:
        print(f"Admin credentials: admin / {admin_password}")
    
    # Additional users
    if args.users:
        for user_spec in args.users:
            if ':' in user_spec:
                username, role = user_spec.split(':', 1)
            else:
                username, role = user_spec, 'user'
            
            user_password = generate_secure_password()
            users[username] = create_user_account(username, user_password, role)
            print(f"User credentials: {username} / {user_password}")
    
    # Write to environment file
    users_json = json.dumps(users)
    
    # Update environment variables
    update_env_var('DASHBOARD_USERS', users_json)
    
    # Also set basic auth variables for the admin user  
    if 'admin' in users:
        update_env_var('DASHBOARD_USERNAME', 'admin')
        update_env_var('DASHBOARD_PASSWORD', admin_password)
        update_env_var('DASHBOARD_SESSION_TIMEOUT', '3600')
    
    print(f"✅ User accounts written to .env")

def generate_ssl_certificate(args):
    """Generate self-signed SSL certificate"""
    print("🔒 Generating SSL certificate...")
    
    ssl_dir = Path('ssl')
    ssl_dir.mkdir(exist_ok=True)
    
    cert_path = ssl_dir / 'cert.pem'
    key_path = ssl_dir / 'key.pem'
    
    # Generate certificate
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
        '-keyout', str(key_path),
        '-out', str(cert_path),
        '-days', str(args.cert_days),
        '-nodes',
        '-subj', f'/C=US/ST=State/L=City/O=Organization/CN={args.domain}'
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Set proper permissions
        os.chmod(key_path, 0o600)
        os.chmod(cert_path, 0o644)
        
        print(f"✅ SSL certificate generated:")
        print(f"   Certificate: {cert_path}")
        print(f"   Private key: {key_path}")
        
        # Update environment
        update_env_var('STREAMLIT_SERVER_SSL_CERT_FILE', str(cert_path.absolute()))
        update_env_var('STREAMLIT_SERVER_SSL_KEY_FILE', str(key_path.absolute()))
        update_env_var('STREAMLIT_SERVER_PORT_HTTPS', '443')
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate SSL certificate: {e}")
        print("Make sure OpenSSL is installed: apt-get install openssl")
        sys.exit(1)

def update_env_var(key, value):
    """Update environment variable in .env file with proper formatting"""
    env_path = Path('.env')
    
    # Read existing lines
    env_lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
    
    # Remove existing line with this key and clean up any formatting issues
    cleaned_lines = []
    for line in env_lines:
        # Skip lines that start with our key
        if line.startswith(f'{key}='):
            continue
        # Clean up any malformed lines (missing newlines)
        if not line.endswith('\n') and line.strip():
            line = line.strip() + '\n'
        cleaned_lines.append(line)
    
    # Ensure file ends with newline before adding new content
    if cleaned_lines and not cleaned_lines[-1].endswith('\n'):
        cleaned_lines[-1] = cleaned_lines[-1].rstrip() + '\n'
    
    # Add new line with proper formatting
    cleaned_lines.append(f'{key}={value}\n')
    
    # Write back with proper formatting
    with open(env_path, 'w') as f:
        f.writelines(cleaned_lines)

def generate_tokens(args):
    """Generate authentication tokens"""
    print("🎫 Generating authentication tokens...")
    
    tokens = []
    for i in range(args.token_count):
        token = secrets.token_urlsafe(32)
        tokens.append(token)
        print(f"Token {i+1}: {token}")
    
    # Update environment
    update_env_var('DASHBOARD_TOKENS', ','.join(tokens))
    print(f"✅ {len(tokens)} tokens generated and saved to .env")

def validate_security():
    """Validate security configuration"""
    print("🔍 Validating security configuration...")
    
    issues = []
    
    # Check environment file
    env_path = Path('.env')
    if not env_path.exists():
        issues.append("❌ No .env file found")
    else:
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Check for default password
        if 'DASHBOARD_PASSWORD=admin123' in env_content:
            issues.append("⚠️ Using default password - change it!")
        
        # Check for SSL configuration
        if 'STREAMLIT_SERVER_SSL_CERT_FILE' not in env_content:
            issues.append("💡 No SSL certificate configured")
        
        # Check for session timeout
        if 'DASHBOARD_SESSION_TIMEOUT' not in env_content:
            issues.append("💡 No session timeout configured")
    
    # Check SSL files
    ssl_cert = os.getenv('STREAMLIT_SERVER_SSL_CERT_FILE')
    ssl_key = os.getenv('STREAMLIT_SERVER_SSL_KEY_FILE')
    
    if ssl_cert and not Path(ssl_cert).exists():
        issues.append(f"❌ SSL certificate not found: {ssl_cert}")
    
    if ssl_key and not Path(ssl_key).exists():
        issues.append(f"❌ SSL private key not found: {ssl_key}")
    
    # Report results
    if issues:
        print("\n🔍 Security Issues Found:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ Security configuration looks good!")
    
    return len(issues) == 0

def setup_production_config(args):
    """Setup production configuration"""
    print("🏭 Setting up production configuration...")
    
    # Production environment variables
    prod_config = {
        'DASHBOARD_SESSION_TIMEOUT': '3600',  # 1 hour
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false',
        'STREAMLIT_SERVER_ENABLE_STATIC_SERVING': 'true',
        'STREAMLIT_SERVER_ENABLE_CORS': 'false',
        'STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION': 'true'
    }
    
    for key, value in prod_config.items():
        update_env_var(key, value)
    
    # Create systemd service file
    service_content = f"""[Unit]
Description=Crypto Market Dashboard
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'streamlit')}
WorkingDirectory={Path.cwd()}
Environment=PATH={os.getenv('PATH')}
EnvironmentFile={Path.cwd() / '.env'}
ExecStart=/usr/local/bin/streamlit run monitoring/dashboard.py --server.port=8501
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    service_path = Path('scripts/dashboard.service')
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Production config created:")
    print(f"   Environment: .env")
    print(f"   Service file: {service_path}")
    print(f"\nTo install service:")
    print(f"   sudo cp {service_path} /etc/systemd/system/")
    print(f"   sudo systemctl enable dashboard")
    print(f"   sudo systemctl start dashboard")

def main():
    parser = argparse.ArgumentParser(description='Setup security for Streamlit dashboard')
    
    parser.add_argument('--admin-password', help='Admin password (generated if not provided)')
    parser.add_argument('--users', nargs='*', help='Additional users (format: username[:role])')
    parser.add_argument('--ssl', action='store_true', help='Generate SSL certificate')
    parser.add_argument('--domain', default='localhost', help='Domain for SSL certificate')
    parser.add_argument('--cert-days', type=int, default=365, help='Certificate validity days')
    parser.add_argument('--tokens', type=int, dest='token_count', help='Generate authentication tokens')
    parser.add_argument('--validate', action='store_true', help='Validate security configuration')
    parser.add_argument('--production', action='store_true', help='Setup production configuration')
    
    args = parser.parse_args()
    
    # If no specific action, run basic setup
    if not any([args.ssl, args.token_count, args.validate, args.production]):
        print("🚀 Running basic security setup...")
        setup_users(args)
        args.ssl = True
        args.token_count = 3
    
    # Execute requested actions
    if args.ssl:
        generate_ssl_certificate(args)
    
    if args.token_count:
        generate_tokens(args)
    
    if hasattr(args, 'admin_password') or args.users:
        setup_users(args)
    
    if args.production:
        setup_production_config(args)
    
    if args.validate:
        validate_security()
    
    print("\n🔒 Security setup complete!")
    print("\nNext steps:")
    print("1. Review .env file for your configuration")
    print("2. Start dashboard: streamlit run monitoring/dashboard.py")
    print("3. Visit: https://localhost:8501 (or http://localhost:8501)")
    print("4. Login with your credentials")

if __name__ == '__main__':
    main()