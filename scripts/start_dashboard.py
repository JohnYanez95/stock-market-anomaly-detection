#!/usr/bin/env python3
"""
Automated HTTPS Dashboard Startup Script
Loads SSL configuration and starts Streamlit with proper HTTPS settings
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
        return True
    else:
        print(f"❌ .env file not found at {env_path}")
        return False

def check_ssl_certificates():
    """Verify SSL certificates exist"""
    cert_file = Path('ssl/cert.pem')
    key_file = Path('ssl/key.pem')
    
    if not cert_file.exists():
        print(f"❌ SSL certificate not found: {cert_file}")
        print("Run: python scripts/setup_security.py")
        return False
        
    if not key_file.exists():
        print(f"❌ SSL private key not found: {key_file}")
        print("Run: python scripts/setup_security.py")
        return False
        
    print(f"✅ SSL certificate found: {cert_file}")
    print(f"✅ SSL private key found: {key_file}")
    return True

def setup_https_environment():
    """Configure environment variables for Streamlit HTTPS"""
    # Set absolute paths for SSL files
    base_path = Path(__file__).parent.parent.absolute()
    cert_path = base_path / 'ssl' / 'cert.pem'
    key_path = base_path / 'ssl' / 'key.pem'
    
    # Set Streamlit HTTPS environment variables
    os.environ['STREAMLIT_SERVER_SSL_CERT_FILE'] = str(cert_path)
    os.environ['STREAMLIT_SERVER_SSL_KEY_FILE'] = str(key_path)
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'  # Restrict to localhost only
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'  # Disable for CORS compatibility
    
    print(f"🔒 HTTPS configured:")
    print(f"   Certificate: {cert_path}")
    print(f"   Private Key: {key_path}")
    print(f"   Port: 8501")

def get_credentials():
    """Get login credentials from environment"""
    username = os.getenv('DASHBOARD_USERNAME', 'admin')
    password = os.getenv('DASHBOARD_PASSWORD', 'admin123')
    
    print(f"\n🔑 Login Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    
    return username, password

def start_streamlit():
    """Start Streamlit dashboard with HTTPS"""
    dashboard_path = Path(__file__).parent.parent / 'monitoring' / 'dashboard.py'
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard not found: {dashboard_path}")
        return False
    
    print(f"\n🚀 Starting Streamlit dashboard...")
    print(f"   Dashboard: {dashboard_path}")
    print(f"   HTTPS URL: https://localhost:8501")
    print(f"   Network URL: https://{get_network_ip()}:8501")
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(dashboard_path),
            '--server.headless=true'
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⏹️  Dashboard stopped by user")
        return True

def get_network_ip():
    """Get network IP address for external access"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def main():
    """Main execution function"""
    print("🔒 Secure Streamlit Dashboard Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('monitoring/dashboard.py').exists():
        print("❌ Please run this script from the project root directory")
        print("   cd /path/to/stock-market-anomaly-detection")
        sys.exit(1)
    
    # Load environment
    if not load_environment():
        print("⚠️  Continuing without .env file...")
    
    # Check SSL certificates
    if not check_ssl_certificates():
        print("\n🔧 Setting up security...")
        try:
            subprocess.run([sys.executable, 'scripts/setup_security.py'], check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to run security setup")
            sys.exit(1)
    
    # Setup HTTPS environment
    setup_https_environment()
    
    # Show credentials
    get_credentials()
    
    print("\n" + "=" * 50)
    print("🌐 Access your dashboard at:")
    print("   https://localhost:8501")
    print("\n⚠️  Browser Security Warning:")
    print("   Click 'Advanced' → 'Proceed to localhost'")
    print("   (Self-signed certificate warning is expected)")
    print("=" * 50)
    
    # Start dashboard
    success = start_streamlit()
    
    if success:
        print("\n✅ Dashboard started successfully!")
    else:
        print("\n❌ Failed to start dashboard")
        sys.exit(1)

if __name__ == "__main__":
    main()