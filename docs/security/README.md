# 🔒 Security Documentation

## Overview

This directory contains comprehensive security documentation for the Stock Market Anomaly Detection Dashboard. Our security implementation follows industry best practices to protect sensitive financial data, API credentials, and user sessions.

## 📚 Documentation Structure

### 1. [HTTPS Setup Guide](HTTPS_SETUP.md)
Complete guide for configuring HTTPS/SSL certificates and secure communication.

### 2. Security Components

#### Authentication Module (`monitoring/auth.py`)
- PBKDF2 password hashing with 100,000 iterations
- Session management with configurable timeouts
- Role-based access control (RBAC)
- Token-based authentication support

#### Security Scripts (`scripts/`)
- `setup_security.py` - Automated security configuration
- `change_password.py` - Password management utility
- `test_auth.py` - Authentication system test suite

## 🛡️ Security Features

### 1. **Authentication & Authorization**
- **Multi-factor support**: Username/password + optional tokens
- **Role hierarchy**: admin > manager > user > viewer
- **Session management**: Automatic timeout and activity tracking
- **Secure storage**: Hashed passwords with unique salts

### 2. **Data Protection**
- **API key masking**: Sensitive data hidden in UI
- **Environment isolation**: Credentials in .env files
- **Secure communication**: HTTPS/SSL support
- **Input validation**: Protection against injection attacks

### 3. **Monitoring & Compliance**
- **Access logging**: User login/logout tracking
- **Security warnings**: Environment validation
- **Session tracking**: Active user monitoring
- **Audit trail**: Authentication events

## 🚀 Quick Security Setup

### Step 1: Initial Configuration
```bash
# Activate virtual environment
source venv/bin/activate

# Run security setup
python scripts/setup_security.py

# This generates:
# - Secure admin credentials
# - SSL certificates (self-signed)
# - Environment configuration
# - Authentication tokens (optional)
```

### Step 2: Test Security
```bash
# Run comprehensive security tests
python scripts/test_auth.py

# Expected output:
# ✅ 9 tests passed
# 🎉 Authentication system ready
```

### Step 3: Start Secured Dashboard
```bash
# Launch with authentication
streamlit run monitoring/dashboard.py

# Access at: http://localhost:8501
# Login with generated credentials
```

## 🔑 Common Security Tasks

### Change Password
```bash
# Interactive password change
python scripts/change_password.py

# Direct password change
python scripts/change_password.py --user admin --password "new_secure_pass"
```

### Add Users
```bash
# Add users with specific roles
python scripts/setup_security.py --users "analyst:user" "manager:manager"
```

### Generate API Tokens
```bash
# Create 5 authentication tokens
python scripts/setup_security.py --tokens 5
```

### Enable HTTPS
```bash
# Generate SSL certificate
python scripts/setup_security.py --ssl --domain yourdomain.com

# Or use existing certificates
export STREAMLIT_SERVER_SSL_CERT_FILE=/path/to/cert.pem
export STREAMLIT_SERVER_SSL_KEY_FILE=/path/to/key.pem
```

## 📊 Security Configuration Reference

### Environment Variables (.env)
```env
# Authentication
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_password
DASHBOARD_SESSION_TIMEOUT=3600  # 1 hour

# Multi-user (JSON format)
DASHBOARD_USERS={"admin":{...}, "user":{...}}

# Token authentication
DASHBOARD_TOKENS=token1,token2,token3

# SSL/HTTPS
STREAMLIT_SERVER_PORT_HTTPS=443
STREAMLIT_SERVER_SSL_CERT_FILE=/path/to/cert.pem
STREAMLIT_SERVER_SSL_KEY_FILE=/path/to/key.pem

# API Security
POLYGON_API_KEY=your_api_key  # Automatically masked in UI
```

### Role Permissions
| Role    | Dashboard | Data Export | Settings | User Mgmt |
|---------|-----------|-------------|----------|-----------|
| admin   | ✅        | ✅          | ✅       | ✅        |
| manager | ✅        | ✅          | ✅       | ❌        |
| user    | ✅        | ✅          | ❌       | ❌        |
| viewer  | ✅        | ❌          | ❌       | ❌        |

## 🚨 Security Best Practices

### 1. **Password Policy**
- Minimum 8 characters (enforced)
- Recommended: 16+ characters with mixed case/numbers/symbols
- Change default password immediately
- Use unique passwords for each user

### 2. **Environment Security**
```bash
# Secure .env file permissions
chmod 600 .env

# Never commit .env to git
# .gitignore already includes *.env
```

### 3. **Production Deployment**
- Always use HTTPS in production
- Use reverse proxy (Nginx/Apache) for additional security
- Enable firewall rules for ports 80/443 only
- Regular security updates and monitoring

### 4. **Session Management**
- Configure appropriate timeout (default: 1 hour)
- Force logout on suspicious activity
- Monitor active sessions
- Clear sessions on password change

## 🔍 Security Testing

### Automated Tests
```bash
# Full security test suite
python scripts/test_auth.py

# Tests include:
# ✅ Password hashing
# ✅ User authentication
# ✅ Token validation
# ✅ Session management
# ✅ API key masking
# ✅ Environment validation
```

### Manual Security Checklist
- [ ] Changed default admin password
- [ ] Removed test tokens from production
- [ ] Enabled HTTPS for production
- [ ] Restricted file permissions (.env)
- [ ] Configured firewall rules
- [ ] Reviewed user roles and permissions
- [ ] Tested session timeout
- [ ] Verified API key masking

## 🆘 Troubleshooting

### Common Issues

#### 1. Authentication Failures
```bash
# Check current users
python scripts/change_password.py --list-users

# Verify environment loading
python scripts/test_auth.py

# Reset admin password
python scripts/setup_security.py --admin-password "new_password"
```

#### 2. SSL Certificate Issues
```bash
# Regenerate self-signed certificate
python scripts/setup_security.py --ssl

# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Test HTTPS connection
curl -k https://localhost:8501
```

#### 3. Session Problems
```bash
# Check session timeout setting
grep DASHBOARD_SESSION_TIMEOUT .env

# Clear all sessions (restart dashboard)
pkill -f "streamlit run"
streamlit run monitoring/dashboard.py
```

## 📈 Security Roadmap

### Current Implementation ✅
- Basic authentication system
- Password hashing and salting
- Session management
- Role-based access control
- API key protection
- HTTPS support

### Future Enhancements 🚧
- [ ] Two-factor authentication (2FA)
- [ ] OAuth2/SAML integration
- [ ] Advanced audit logging
- [ ] Intrusion detection
- [ ] Rate limiting
- [ ] Security headers enhancement

## 🤝 Contributing

When contributing security features:
1. Follow OWASP guidelines
2. Add comprehensive tests
3. Update documentation
4. Never log sensitive data
5. Use secure defaults
6. Consider backwards compatibility

## 📞 Security Contact

For security issues or vulnerabilities:
1. Do not create public issues
2. Document the vulnerability
3. Test the fix locally
4. Submit a private security advisory

---

*Last updated: September 23, 2025*
*Security is a continuous process - stay vigilant!* 🛡️