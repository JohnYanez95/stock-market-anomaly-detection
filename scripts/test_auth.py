#!/usr/bin/env python3
"""
Authentication System Test Script

Tests the complete authentication system without starting the dashboard.
This validates all security components and environment configuration.

Usage:
    python scripts/test_auth.py
"""

import sys
import os
from pathlib import Path
import json

# Add monitoring to path
sys.path.append('monitoring')

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ No .env file found")
        return False
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
                os.environ[key] = value
    
    print(f"✅ Loaded {len(env_vars)} environment variables from .env")
    return True

def test_auth_module_import():
    """Test if authentication module can be imported"""
    try:
        from auth import DashboardAuth, require_authentication, mask_api_key, validate_environment
        print("✅ Authentication module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import authentication module: {e}")
        return False

def test_password_hashing():
    """Test password hashing and verification"""
    try:
        from auth import DashboardAuth
        
        auth = DashboardAuth()
        
        # Test password hashing
        password = "test123"
        hashed_password, salt = auth.hash_password(password)
        
        print(f"✅ Password hashing works - hash length: {len(hashed_password)}, salt length: {len(salt)}")
        
        # Test verification
        is_valid = auth.verify_password(password, hashed_password, salt)
        if is_valid:
            print("✅ Password verification works")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test wrong password
        is_invalid = auth.verify_password("wrong", hashed_password, salt)
        if not is_invalid:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password was accepted")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Password hashing test failed: {e}")
        return False

def test_credentials_loading():
    """Test credential loading from environment"""
    try:
        from auth import DashboardAuth
        
        auth = DashboardAuth()
        credentials = auth.get_credentials()
        
        print(f"✅ Credentials loaded: {len(credentials)} user(s)")
        
        for username, user_data in credentials.items():
            print(f"   - {username}: role={user_data.get('role', 'unknown')}")
            
            # Validate required fields
            required_fields = ['password_hash', 'salt', 'role']
            for field in required_fields:
                if field not in user_data:
                    print(f"❌ Missing required field '{field}' for user {username}")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Credentials loading test failed: {e}")
        return False

def test_user_authentication():
    """Test user authentication with actual credentials"""
    try:
        from auth import DashboardAuth
        
        auth = DashboardAuth()
        
        # Get admin password from environment
        admin_password = os.getenv('DASHBOARD_PASSWORD')
        if not admin_password:
            print("⚠️ No DASHBOARD_PASSWORD set, using default")
            admin_password = "***REDACTED***"
        
        # Test admin authentication
        result = auth.authenticate_user('admin', admin_password)
        if result:
            print(f"✅ Admin authentication successful with password: {admin_password}")
        else:
            print(f"❌ Admin authentication failed with password: {admin_password}")
            
            # Debug: Check what credentials are available
            credentials = auth.get_credentials()
            admin_data = credentials.get('admin', {})
            if admin_data:
                # Test with manual verification
                manual_result = auth.verify_password(
                    admin_password, 
                    admin_data['password_hash'], 
                    admin_data['salt']
                )
                print(f"   Manual verification result: {manual_result}")
                print(f"   Password hash (first 20 chars): {admin_data['password_hash'][:20]}...")
                print(f"   Salt (first 20 chars): {admin_data['salt'][:20]}...")
            return False
        
        # Test wrong credentials
        wrong_result = auth.authenticate_user('admin', 'wrongpassword')
        if not wrong_result:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password was accepted")
            return False
        
        # Test non-existent user
        fake_result = auth.authenticate_user('fakeuser', 'password')
        if not fake_result:
            print("✅ Non-existent user correctly rejected")
        else:
            print("❌ Non-existent user was accepted")
            return False
        
        return True
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_authentication():
    """Test token-based authentication"""
    try:
        from auth import DashboardAuth
        
        auth = DashboardAuth()
        
        # Check if tokens are configured
        tokens = os.getenv('DASHBOARD_TOKENS', '').split(',')
        tokens = [t.strip() for t in tokens if t.strip()]
        
        if not tokens:
            print("⚠️ No authentication tokens configured")
            return True  # Not an error, just not configured
        
        # Test valid token
        valid_result = auth.authenticate_token(tokens[0])
        if valid_result:
            print(f"✅ Token authentication works - tested with {tokens[0][:10]}...")
        else:
            print(f"❌ Token authentication failed")
            return False
        
        # Test invalid token
        invalid_result = auth.authenticate_token('invalid_token')
        if not invalid_result:
            print("✅ Invalid token correctly rejected")
        else:
            print("❌ Invalid token was accepted")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Token authentication test failed: {e}")
        return False

def test_api_key_masking():
    """Test API key masking functionality"""
    try:
        from auth import mask_api_key
        
        # Test with real API key from environment
        api_key = os.getenv('POLYGON_API_KEY', 'test_api_key_1234567890')
        masked = mask_api_key(api_key)
        
        if len(masked) > 0 and '*' in masked:
            print(f"✅ API key masking works: {api_key} -> {masked}")
        else:
            print(f"❌ API key masking failed: {masked}")
            return False
        
        # Test edge cases
        short_key = "abc"
        masked_short = mask_api_key(short_key)
        if masked_short == "****":
            print("✅ Short API key correctly masked")
        else:
            print(f"❌ Short API key masking failed: {masked_short}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ API key masking test failed: {e}")
        return False

def test_environment_validation():
    """Test security environment validation"""
    try:
        from auth import validate_environment
        
        warnings = validate_environment()
        
        print(f"✅ Environment validation complete - {len(warnings)} warning(s)")
        for warning in warnings:
            print(f"   {warning}")
        
        return True
    except Exception as e:
        print(f"❌ Environment validation test failed: {e}")
        return False

def test_session_management():
    """Test session management functionality"""
    try:
        from auth import DashboardAuth
        import time
        
        auth = DashboardAuth()
        
        # Mock session state (normally provided by Streamlit)
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def __setattr__(self, name, value):
                if name == 'data':
                    super().__setattr__(name, value)
                else:
                    self.data[name] = value
            
            def __getattr__(self, name):
                return self.data.get(name)
            
            def __delattr__(self, name):
                if name in self.data:
                    del self.data[name]
        
        # Mock streamlit session state
        import sys
        mock_st = type(sys)('streamlit')
        mock_st.session_state = MockSessionState()
        sys.modules['streamlit'] = mock_st
        
        # Test session creation
        auth.create_session('testuser')
        
        # Check session validity
        if auth.is_session_valid():
            print("✅ Session creation and validation works")
        else:
            print("❌ Session validation failed")
            return False
        
        # Test session info
        session_info = auth.get_session_info()
        if session_info and 'username' in session_info:
            print(f"✅ Session info works: user={session_info['username']}")
        else:
            print("❌ Session info failed")
            return False
        
        # Test logout
        auth.logout()
        if not auth.is_session_valid():
            print("✅ Session logout works")
        else:
            print("❌ Session logout failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all authentication tests"""
    print("🔒 Authentication System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Loading", load_environment),
        ("Module Import", test_auth_module_import),
        ("Password Hashing", test_password_hashing),
        ("Credentials Loading", test_credentials_loading),
        ("User Authentication", test_user_authentication),
        ("Token Authentication", test_token_authentication),
        ("API Key Masking", test_api_key_masking),
        ("Environment Validation", test_environment_validation),
        ("Session Management", test_session_management),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Authentication system is ready.")
        print("\nTo start the secured dashboard:")
        print("  streamlit run monitoring/dashboard.py")
        print("  Default credentials: admin / securepassword123")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        
        # Show environment debug info
        print("\n🔍 Environment Debug Info:")
        env_vars = ['DASHBOARD_USERNAME', 'DASHBOARD_PASSWORD', 'DASHBOARD_USERS', 'POLYGON_API_KEY']
        for var in env_vars:
            value = os.getenv(var, 'Not set')
            if var == 'POLYGON_API_KEY' and value != 'Not set':
                value = f"{value[:4]}***{value[-4:]}"
            elif var == 'DASHBOARD_PASSWORD' and value != 'Not set':
                value = "***SET***"
            print(f"  {var}: {value}")
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)