#!/usr/bin/env python3
"""
Streamlit Authentication Module

Provides authentication and security features for the Streamlit dashboard.
Supports multiple authentication methods:
- Basic username/password authentication
- Token-based authentication
- Session management
- API key security

Usage:
    from monitoring.auth import require_authentication, is_authenticated
    
    if not require_authentication():
        st.stop()
"""

import streamlit as st
import hashlib
import hmac
import os
from typing import Optional, Dict, Any
import json
import time
from datetime import datetime, timedelta

class DashboardAuth:
    """Authentication manager for Streamlit dashboard"""
    
    def __init__(self):
        self.session_timeout = int(os.getenv('DASHBOARD_SESSION_TIMEOUT', '3600'))  # 1 hour default
        
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt for secure storage"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        # Use PBKDF2 for password hashing
        key = hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 salt.encode('utf-8'), 
                                 100000)  # 100,000 iterations
        return key.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against stored hash"""
        key, _ = self.hash_password(password, salt)
        return hmac.compare_digest(key, hashed_password)
    
    def get_credentials(self) -> Dict[str, Dict[str, str]]:
        """Get authentication credentials from environment"""
        # Default admin user
        admin_user = os.getenv('DASHBOARD_USERNAME', 'admin')
        admin_pass = os.getenv('DASHBOARD_PASSWORD', 'admin123')
        
        # Hash the default password if not already hashed
        if not os.getenv('DASHBOARD_PASSWORD_HASHED'):
            hashed_pass, salt = self.hash_password(admin_pass)
        else:
            hashed_pass = os.getenv('DASHBOARD_PASSWORD_HASHED')
            salt = os.getenv('DASHBOARD_PASSWORD_SALT')
        
        # Support for multiple users (JSON format in env var)
        users_json = os.getenv('DASHBOARD_USERS')
        if users_json:
            try:
                users = json.loads(users_json)
                return users
            except json.JSONDecodeError:
                st.error("Invalid DASHBOARD_USERS JSON format")
        
        # Default single user
        return {
            admin_user: {
                'password_hash': hashed_pass,
                'salt': salt,
                'role': 'admin',
                'created': datetime.now().isoformat()
            }
        }
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        credentials = self.get_credentials()
        
        if username not in credentials:
            return False
        
        user_data = credentials[username]
        return self.verify_password(
            password, 
            user_data['password_hash'], 
            user_data['salt']
        )
    
    def authenticate_token(self, token: str) -> bool:
        """Authenticate using bearer token"""
        valid_tokens = os.getenv('DASHBOARD_TOKENS', '').split(',')
        valid_tokens = [t.strip() for t in valid_tokens if t.strip()]
        
        if not valid_tokens:
            return False
        
        return token in valid_tokens
    
    def create_session(self, username: str) -> None:
        """Create authenticated session"""
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.login_time = time.time()
        st.session_state.last_activity = time.time()
        
        # Store user data
        credentials = self.get_credentials()
        if username in credentials:
            st.session_state.user_role = credentials[username].get('role', 'user')
        else:
            st.session_state.user_role = 'user'
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        if not getattr(st.session_state, 'authenticated', False):
            return False
        
        # Check session timeout
        if hasattr(st.session_state, 'last_activity'):
            if time.time() - st.session_state.last_activity > self.session_timeout:
                self.logout()
                return False
        
        # Update last activity
        st.session_state.last_activity = time.time()
        return True
    
    def logout(self) -> None:
        """Clear session and logout user"""
        for key in ['authenticated', 'username', 'login_time', 'last_activity', 'user_role']:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        if not self.is_session_valid():
            return {}
        
        current_time = time.time()
        login_time = getattr(st.session_state, 'login_time', current_time)
        last_activity = getattr(st.session_state, 'last_activity', current_time)
        
        # Update last activity to current time for display purposes
        st.session_state.last_activity = current_time
        
        session_duration = int(current_time - login_time)
        time_since_activity = int(current_time - last_activity)
        timeout_remaining = max(0, int(self.session_timeout - time_since_activity))
        
        return {
            'username': getattr(st.session_state, 'username', 'unknown'),
            'role': getattr(st.session_state, 'user_role', 'user'),
            'login_time': datetime.fromtimestamp(login_time).isoformat(),
            'session_duration': session_duration,
            'timeout_in': timeout_remaining
        }

def render_login_form() -> bool:
    """Render login form and handle authentication"""
    auth = DashboardAuth()
    
    st.markdown("""
    <div style="max-width: 400px; margin: 100px auto; padding: 20px; 
                border: 1px solid #ddd; border-radius: 10px; 
                background-color: #f9f9f9;">
    """, unsafe_allow_html=True)
    
    st.markdown("# 🔐 Dashboard Login")
    st.markdown("---")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("Login", use_container_width=True)
        with col2:
            token_auth = st.checkbox("Use Token Auth")
    
    # Token authentication section
    if token_auth:
        st.markdown("### Token Authentication")
        token = st.text_input("Bearer Token", type="password", placeholder="Enter authentication token")
        if st.button("Authenticate with Token"):
            if auth.authenticate_token(token):
                auth.create_session('token_user')
                st.success("✅ Token authentication successful!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid token")
    
    # Handle login
    if login_button:
        if not username or not password:
            st.error("Please enter both username and password")
        elif auth.authenticate_user(username, password):
            auth.create_session(username)
            st.success(f"✅ Welcome back, {username}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
            st.info("💡 Default credentials: admin / admin123")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Security information
    with st.expander("🔒 Security Information"):
        st.markdown("""
        **Security Features:**
        - PBKDF2 password hashing with 100,000 iterations
        - Session timeout (configurable, default: 1 hour)
        - HMAC-based password comparison
        - Bearer token authentication support
        - Environment-based credential management
        
        **Configuration:**
        - Set `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` environment variables
        - Use `DASHBOARD_TOKENS` for token-based authentication
        - Configure `DASHBOARD_SESSION_TIMEOUT` in seconds
        """)
    
    return False

def render_session_info():
    """Render session information in sidebar"""
    auth = DashboardAuth()
    session_info = auth.get_session_info()
    
    if session_info:
        st.sidebar.markdown("### 👤 Session Info")
        st.sidebar.markdown(f"**User:** {session_info['username']}")
        st.sidebar.markdown(f"**Role:** {session_info['role']}")
        
        # Format duration nicely
        duration = session_info['session_duration']
        duration_str = f"{duration//3600}h {(duration%3600)//60}m {duration%60}s" if duration >= 3600 else f"{duration//60}m {duration%60}s"
        st.sidebar.markdown(f"**Duration:** {duration_str}")
        
        # Format timeout remaining nicely  
        timeout = session_info['timeout_in']
        if timeout > 0:
            timeout_str = f"{timeout//3600}h {(timeout%3600)//60}m {timeout%60}s" if timeout >= 3600 else f"{timeout//60}m {timeout%60}s"
            st.sidebar.markdown(f"**Timeout in:** {timeout_str}")
        else:
            st.sidebar.markdown(f"**Timeout in:** ⚠️ Session expired")
        
        if st.sidebar.button("🚪 Logout"):
            auth.logout()
            st.rerun()

def require_authentication() -> bool:
    """Main authentication check - call at start of dashboard"""
    auth = DashboardAuth()
    
    # Check if user is already authenticated
    if auth.is_session_valid():
        render_session_info()
        return True
    
    # Show login form
    render_login_form()
    return False

def is_authenticated() -> bool:
    """Simple check if user is authenticated"""
    auth = DashboardAuth()
    return auth.is_session_valid()

def get_current_user() -> Optional[str]:
    """Get current authenticated user"""
    if is_authenticated():
        return getattr(st.session_state, 'username', None)
    return None

def require_role(required_role: str) -> bool:
    """Check if current user has required role"""
    if not is_authenticated():
        return False
    
    user_role = getattr(st.session_state, 'user_role', 'user')
    
    # Simple role hierarchy
    role_hierarchy = {'admin': 3, 'manager': 2, 'user': 1, 'viewer': 0}
    
    required_level = role_hierarchy.get(required_role, 0)
    user_level = role_hierarchy.get(user_role, 0)
    
    return user_level >= required_level

def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """Mask API key for display purposes"""
    if not api_key or len(api_key) <= visible_chars * 2:
        return "****"
    
    return f"{api_key[:visible_chars]}{'*' * (len(api_key) - visible_chars * 2)}{api_key[-visible_chars:]}"

# Security utilities
def validate_environment():
    """Validate security environment configuration"""
    warnings = []
    
    # Check if using default credentials
    if os.getenv('DASHBOARD_PASSWORD', 'admin123') == 'admin123':
        warnings.append("⚠️ Using default password - change DASHBOARD_PASSWORD environment variable")
    
    # Check session timeout
    timeout = int(os.getenv('DASHBOARD_SESSION_TIMEOUT', '3600'))
    if timeout > 7200:  # 2 hours
        warnings.append("⚠️ Session timeout is quite long - consider reducing for better security")
    
    # Check if HTTPS is configured (for production)
    if not os.getenv('STREAMLIT_SERVER_PORT_HTTPS'):
        warnings.append("💡 Consider configuring HTTPS for production deployment")
    
    return warnings