# HTTPS Setup for Streamlit Dashboard

## Overview

This comprehensive guide covers authentication, authorization, and HTTPS/SSL configuration for the Streamlit dashboard in production environments. Our security implementation protects sensitive financial data, API keys, and user sessions using industry-standard practices.

## 🚀 Quick Start Guide

### 1. Basic Security Setup (5 minutes)

```bash
# Activate virtual environment
source venv/bin/activate

# Run automated security setup
python scripts/setup_security.py

# This will:
# ✅ Generate secure admin credentials
# ✅ Configure session management
# ✅ Set up environment variables
# ✅ Create self-signed SSL certificate

# Start the secured dashboard
streamlit run monitoring/dashboard.py
```

### 2. Default Credentials
- **Username**: admin
- **Password**: Will be displayed during setup (or check .env file)
- **Session timeout**: 1 hour (configurable)

### 3. Change Default Password
```bash
python scripts/change_password.py
# Enter new password when prompted
```

### 4. Access Dashboard
- **HTTP**: http://localhost:8501 (development)
- **HTTPS**: https://localhost:8501 (with SSL setup)

## 🔐 Authentication System

### Features
- **PBKDF2 password hashing** with 100,000 iterations
- **Salt-based security** preventing rainbow table attacks
- **Session management** with configurable timeouts
- **Role-based access control** (admin, manager, user, viewer)
- **Token-based authentication** for API access
- **API key masking** in UI displays

### Configuration Options

#### Basic Configuration (.env file)
```env
# Simple setup (single admin user)
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password
DASHBOARD_SESSION_TIMEOUT=3600  # seconds (1 hour)

# Multi-user setup (JSON format)
DASHBOARD_USERS={"admin":{"password_hash":"...","salt":"...","role":"admin"},"analyst":{"password_hash":"...","salt":"...","role":"user"}}

# Token-based authentication
DASHBOARD_TOKENS=token1,token2,token3
```

#### User Management Commands
```bash
# Add new users with roles
python scripts/setup_security.py --users "analyst:user" "manager:manager"

# Change password for existing user
python scripts/change_password.py --user admin --password "new_secure_password"

# List all users
python scripts/change_password.py --list-users

# Generate authentication tokens
python scripts/setup_security.py --tokens 5
```

### Security Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Login    │────▶│  Authentication │────▶│ Session Created │
│  (Streamlit UI) │     │    Module       │     │   (1hr TTL)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Password Input  │     │  PBKDF2 Hash    │     │ Session State   │
│  (Masked)       │     │  Verification   │     │  Management     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## SSL Certificate Options

### 1. Self-Signed Certificates (Development/Testing)

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update environment variables
export STREAMLIT_SERVER_PORT_HTTPS=443
export STREAMLIT_SERVER_SSL_CERT_FILE=/path/to/cert.pem
export STREAMLIT_SERVER_SSL_KEY_FILE=/path/to/key.pem
```

### 2. Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate (replace yourdomain.com)
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in /etc/letsencrypt/live/yourdomain.com/
export STREAMLIT_SERVER_SSL_CERT_FILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
export STREAMLIT_SERVER_SSL_KEY_FILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### 3. Commercial SSL Certificate

```bash
# Use certificates from your SSL provider
export STREAMLIT_SERVER_SSL_CERT_FILE=/path/to/your/certificate.pem
export STREAMLIT_SERVER_SSL_KEY_FILE=/path/to/your/private.key
```

## Streamlit HTTPS Configuration

### Environment Variables

Add to your `.env` file:

```env
# HTTPS Configuration
STREAMLIT_SERVER_PORT_HTTPS=443
STREAMLIT_SERVER_SSL_CERT_FILE=/path/to/cert.pem
STREAMLIT_SERVER_SSL_KEY_FILE=/path/to/key.pem

# Redirect HTTP to HTTPS
STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Streamlit Configuration File

Create `.streamlit/config.toml`:

```toml
[server]
port = 443
enableCORS = false
enableXsrfProtection = true
enableStaticServing = true

# SSL Configuration
sslCertFile = "/path/to/cert.pem"
sslKeyFile = "/path/to/key.pem"

[browser]
gatherUsageStats = false
```

## Production Deployment Options

### Option 1: Direct Streamlit HTTPS

```bash
# Run Streamlit with HTTPS
streamlit run monitoring/dashboard.py \
    --server.port=443 \
    --server.sslCertFile=/path/to/cert.pem \
    --server.sslKeyFile=/path/to/key.pem
```

### Option 2: Reverse Proxy (Recommended)

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### Apache Configuration

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    # Security headers
    Header always set Strict-Transport-Security "max-age=63072000"
    Header always set X-Frame-Options DENY
    Header always set X-Content-Type-Options nosniff
    
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass / http://127.0.0.1:8501/
    ProxyPassReverse / http://127.0.0.1:8501/
    
    # WebSocket support
    ProxyPass /ws ws://127.0.0.1:8501/ws
    ProxyPassReverse /ws ws://127.0.0.1:8501/ws
</VirtualHost>
```

## Docker HTTPS Configuration

### Dockerfile with SSL

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create SSL directory
RUN mkdir -p /app/ssl

# Expose HTTPS port
EXPOSE 443

# Environment variables
ENV STREAMLIT_SERVER_PORT_HTTPS=443
ENV STREAMLIT_SERVER_SSL_CERT_FILE=/app/ssl/cert.pem
ENV STREAMLIT_SERVER_SSL_KEY_FILE=/app/ssl/key.pem

CMD ["streamlit", "run", "monitoring/dashboard.py", "--server.port=443"]
```

### Docker Compose with SSL

```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./ssl:/app/ssl:ro
      - ./data:/app/data
    environment:
      - STREAMLIT_SERVER_PORT_HTTPS=443
      - STREAMLIT_SERVER_SSL_CERT_FILE=/app/ssl/cert.pem
      - STREAMLIT_SERVER_SSL_KEY_FILE=/app/ssl/key.pem
      - DASHBOARD_USERNAME=admin
      - DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}
    restart: unless-stopped
```

## Security Best Practices

### 1. Certificate Management

```bash
# Set proper permissions
sudo chmod 600 /path/to/key.pem
sudo chmod 644 /path/to/cert.pem

# Automated renewal (Let's Encrypt)
0 2 * * * /usr/bin/certbot renew --quiet && systemctl restart nginx
```

### 2. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8501/tcp  # Block direct access to Streamlit

# iptables
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 8501 -j DROP
```

### 3. Environment Security

```bash
# Secure environment file
chmod 600 .env

# Use Docker secrets (production)
echo "your_password" | docker secret create dashboard_password -
```

## Monitoring and Logging

### SSL Certificate Monitoring

```bash
# Check certificate expiration
openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"

# Automated monitoring script
#!/bin/bash
CERT_FILE="/path/to/cert.pem"
DAYS_WARN=30

EXPIRY_DATE=$(openssl x509 -in "$CERT_FILE" -text -noout | grep "Not After" | awk '{print $4 " " $5 " " $7}')
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_WARN ]; then
    echo "WARNING: SSL certificate expires in $DAYS_LEFT days"
fi
```

### Access Logging

```python
# Add to dashboard.py
import logging

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/dashboard.log'),
        logging.StreamHandler()
    ]
)

# Log authentication events
logger.info(f"User {username} logged in from {st.session_state.get('remote_addr', 'unknown')}")
```

## Testing HTTPS Setup

### SSL Configuration Test

```bash
# Test SSL configuration
curl -I https://yourdomain.com

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# SSL Labs test (online)
# Visit: https://www.ssllabs.com/ssltest/
```

### Security Headers Test

```bash
# Test security headers
curl -I https://yourdomain.com

# Expected headers:
# Strict-Transport-Security: max-age=63072000
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Fix SSL file permissions
   sudo chown streamlit:streamlit /path/to/cert.pem /path/to/key.pem
   sudo chmod 600 /path/to/key.pem
   ```

2. **Port 443 Already in Use**
   ```bash
   # Check what's using port 443
   sudo netstat -tlnp | grep :443
   sudo ss -tlnp | grep :443
   ```

3. **Certificate Verification Failed**
   ```bash
   # Check certificate validity
   openssl x509 -in /path/to/cert.pem -text -noout
   openssl verify /path/to/cert.pem
   ```

4. **WebSocket Issues with Reverse Proxy**
   - Ensure WebSocket upgrade headers are properly configured
   - Test WebSocket connection: `wscat -c wss://yourdomain.com/_stcore/stream`

### Debug Mode

```bash
# Run with debug logging
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run monitoring/dashboard.py --logger.level=debug
```

## Production Checklist

- [ ] SSL certificate installed and valid
- [ ] HTTPS redirect configured
- [ ] Security headers implemented
- [ ] Firewall rules configured
- [ ] Strong passwords/tokens configured
- [ ] Session timeout configured
- [ ] Access logging enabled
- [ ] Certificate auto-renewal configured
- [ ] Backup authentication method tested
- [ ] Security scanning completed